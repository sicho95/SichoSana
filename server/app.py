"""SichoSana API NAS : SQLite, synchronisation avec révisions, push opt-in."""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("SICHOSANA_DB_PATH", "/data/sichosana.sqlite3"))
REGISTRATION = os.getenv("SICHOSANA_REGISTRATION_ENABLED", "0") == "1"
VAPID_PUBLIC = os.getenv("SICHOSANA_VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE = os.getenv("SICHOSANA_VAPID_PRIVATE_KEY", "")
VAPID_EMAIL = os.getenv("SICHOSANA_VAPID_EMAIL", "")
app = FastAPI(title="SichoSana Sync", version="0.1.0", docs_url=None, redoc_url=None)

@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=20)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=10000")
    try:
        yield db
    finally:
        db.close()

def setup():
    with connection() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
            salt BLOB NOT NULL, password_hash BLOB NOT NULL, created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tokens (
            token_hash TEXT PRIMARY KEY, account_id TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS states (
            account_id TEXT PRIMARY KEY, revision INTEGER NOT NULL DEFAULT 0,
            content TEXT NOT NULL, updated_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            account_id TEXT NOT NULL, endpoint TEXT NOT NULL,
            content TEXT NOT NULL, created_at INTEGER NOT NULL,
            PRIMARY KEY(account_id, endpoint)
        );
        """)
        db.commit()

@app.on_event("startup")
def startup():
    setup()

class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=12, max_length=256)

class ClientState(BaseModel):
    revision: int = Field(ge=0)
    state: dict[str, Any]

class PushBody(BaseModel):
    subscription: dict[str, Any]

def normalize(name: str) -> str:
    name = name.strip().lower()
    if not re.fullmatch("[a-z0-9][a-z0-9_.-]{2,63}", name):
        raise HTTPException(422, "Identifiant : lettres, chiffres, point, tiret et _")
    return name

def password_hash(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)

def new_token(db: sqlite3.Connection, account_id: str) -> str:
    token = secrets.token_urlsafe(36)
    db.execute("INSERT INTO tokens(token_hash,account_id,expires_at) VALUES(?,?,?)",
               (hashlib.sha256(token.encode()).hexdigest(), account_id, int(time.time()) + 90 * 86400))
    return token

def owner(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentification requise")
    token = authorization[7:]
    if not 36 <= len(token) <= 256:
        raise HTTPException(401, "Jeton invalide")
    digest = hashlib.sha256(token.encode()).hexdigest()
    with connection() as db:
        row = db.execute("SELECT account_id FROM tokens WHERE token_hash=? AND expires_at>?",
                         (digest, int(time.time()))).fetchone()
    if not row:
        raise HTTPException(401, "Connexion expirée ou invalide")
    return str(row["account_id"])

@app.get("/api/v1/health")
def health():
    return {"service": "sichosana-sync", "ok": True, "schema": 1}

@app.post("/api/v1/auth/register")
def register(data: Credentials):
    if not REGISTRATION:
        raise HTTPException(403, "Création de compte désactivée sur le NAS")
    name = normalize(data.username)
    salt = secrets.token_bytes(16)
    account_id = secrets.token_hex(16)
    with connection() as db:
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO accounts VALUES(?,?,?,?,?)",
                       (account_id, name, salt, password_hash(data.password, salt), int(time.time())))
            db.execute("INSERT INTO states VALUES(?,?,?,?)", (account_id, 0, "null", int(time.time())))
            token = new_token(db, account_id)
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            raise HTTPException(409, "Identifiant déjà utilisé")
    return {"token": token, "username": name, "expiresInDays": 90}

@app.post("/api/v1/auth/login")
def login(data: Credentials):
    name = normalize(data.username)
    with connection() as db:
        user = db.execute("SELECT * FROM accounts WHERE username=?", (name,)).fetchone()
        if not user:
            password_hash(data.password, b"\0" * 16)
            raise HTTPException(401, "Identifiant ou mot de passe incorrect")
        if not hmac.compare_digest(password_hash(data.password, user["salt"]), user["password_hash"]):
            raise HTTPException(401, "Identifiant ou mot de passe incorrect")
        token = new_token(db, user["id"])
        db.commit()
    return {"token": token, "username": name, "expiresInDays": 90}

@app.get("/api/v1/state")
def get_state(account_id: str = Depends(owner)):
    with connection() as db:
        row = db.execute("SELECT revision,content FROM states WHERE account_id=?", (account_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Compte non trouvé")
    return {"revision": row["revision"], "state": json.loads(row["content"])}

@app.put("/api/v1/state")
def put_state(data: ClientState, account_id: str = Depends(owner)):
    payload = data.state
    if (payload.get("version") != 1 or not isinstance(payload.get("profiles"), list)
        or not isinstance(payload.get("logs"), list)
        or len(payload["profiles"]) > 20 or len(payload["logs"]) > 100000):
        raise HTTPException(422, "État incompatible")
    ids = [row.get("id") for row in payload["profiles"] if isinstance(row, dict)]
    if len(ids) != len(payload["profiles"]) or not all(isinstance(i, str) and 1 <= len(i) <= 100 for i in ids):
        raise HTTPException(422, "Profils invalides")
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode()) > 1000000:
        raise HTTPException(413, "État trop volumineux")
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT revision FROM states WHERE account_id=?", (account_id,)).fetchone()
        if row is None:
            db.rollback()
            raise HTTPException(404, "Compte non trouvé")
        if row["revision"] != data.revision:
            db.rollback()
            raise HTTPException(409, "Révision divergente : fusion nécessaire")
        next_rev = row["revision"] + 1
        db.execute("UPDATE states SET revision=?,content=?,updated_at=? WHERE account_id=?",
                   (next_rev, encoded, int(time.time()), account_id))
        db.commit()
    return {"revision": next_rev}

@app.get("/api/v1/push/key")
def push_key(account_id: str = Depends(owner)):
    return {"publicKey": VAPID_PUBLIC or None, "configured": bool(VAPID_PUBLIC and VAPID_PRIVATE)}

@app.post("/api/v1/push/subscriptions")
def push_subscribe(data: PushBody, account_id: str = Depends(owner)):
    sub = data.subscription
    endpoint = sub.get("endpoint")
    keys = sub.get("keys") or {}
    if (not VAPID_PUBLIC or not VAPID_PRIVATE
        or not isinstance(endpoint, str) or len(endpoint) > 2048
        or urlparse(endpoint).scheme != "https"
        or not isinstance(keys.get("p256dh"), str)
        or not isinstance(keys.get("auth"), str)):
        raise HTTPException(422, "Abonnement push invalide ou serveur non configuré")
    with connection() as db:
        count = db.execute("SELECT count(*) FROM push_subscriptions WHERE account_id=?", (account_id,)).fetchone()[0]
        exists = db.execute("SELECT 1 FROM push_subscriptions WHERE account_id=? AND endpoint=?",
                            (account_id, endpoint)).fetchone()
        if count >= 12 and not exists:
            raise HTTPException(429, "Trop d'appareils abonnés")
        db.execute("INSERT OR REPLACE INTO push_subscriptions VALUES(?,?,?,?)",
                   (account_id, endpoint, json.dumps(sub), int(time.time())))
        db.commit()
    return {"ok": True}

@app.post("/api/v1/push/test")
def push_test(account_id: str = Depends(owner)):
    if not VAPID_PRIVATE or not VAPID_EMAIL:
        raise HTTPException(503, "Configuration VAPID incomplète")
    from pywebpush import webpush
    with connection() as db:
        rows = db.execute("SELECT content FROM push_subscriptions WHERE account_id=?", (account_id,)).fetchall()
    sent, failed = 0, 0
    for row in rows:
        try:
            webpush(subscription_info=json.loads(row["content"]),
                    data=json.dumps({"title": "SichoSana", "body": "Une petite pause rien que pour toi."}),
                    vapid_private_key=VAPID_PRIVATE,
                    vapid_claims={"sub": "mailto:" + VAPID_EMAIL})
            sent += 1
        except Exception:
            failed += 1
    return {"sent": sent, "failed": failed}

# Le frontend doit rester monté après les routes API.
app.mount("/", StaticFiles(directory=str(ROOT / "static"), html=True), name="frontend")
