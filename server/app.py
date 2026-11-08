"""SichoSana: serveur Python sans dépendances tierces, SQLite et PWA locale.
Aucun routage Cloudflare/Tailscale n'est modifié par ce service.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import mimetypes
import os
from pathlib import Path
import secrets
import sqlite3
import threading
import time
from collections import defaultdict, deque
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote, parse_qs
from server import accounts, astrology

BASE = Path(__file__).resolve().parents[1]
STATIC = Path(os.environ.get("SICHOSANA_WEB_ROOT", BASE / "static")).resolve()
DATA_DIR = Path(os.environ.get("SICHOSANA_DATA_DIR", BASE / ".data")).resolve()
DB_PATH = DATA_DIR / "sichosana.sqlite3"
HOST = os.environ.get("SICHOSANA_HOST", "0.0.0.0")
PORT = int(os.environ.get("SICHOSANA_PORT", "8080"))
LOCK = threading.RLock()
RATE = defaultdict(deque)
LOGGER = logging.getLogger("sichosana")
MAX_JSON = 1_200_000


def connection():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=10000")
    return c


def initialize():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK, connection() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS groups (
            id TEXT PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            salt BLOB NOT NULL,
            password_hash BLOB NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS devices (
            token_hash TEXT PRIMARY KEY,
            group_id TEXT NOT NULL REFERENCES groups(id),
            device_id TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS snapshots (
            group_id TEXT PRIMARY KEY REFERENCES groups(id),
            revision INTEGER NOT NULL DEFAULT 0,
            payload TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS poses (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            origin TEXT NOT NULL,
            asset_license TEXT,
            imported_at INTEGER NOT NULL
        );
        """)
        count = c.execute("SELECT COUNT(*) FROM poses").fetchone()[0]
        if count == 0:
            src = STATIC / "data" / "yoga.json"
            if src.exists():
                for pose in json.loads(src.read_text(encoding="utf-8"))["poses"]:
                    c.execute(
                        "INSERT INTO poses(id,data,origin,asset_license,imported_at) VALUES(?,?,?,?,?)",
                        (pose["id"], json.dumps(pose, ensure_ascii=False), "sichosana-curated", None, int(time.time()))
                    )
        accounts.init_schema(c)
        # Chargé depuis un instantané figé versionné, et jamais depuis une API pendant la pratique.
        frozen = STATIC / "data" / "yoga-api-library.json"
        if frozen.is_file():
            for pose in json.loads(frozen.read_text(encoding="utf-8")).get("poses",[]):
                c.execute("INSERT INTO poses(id,data,origin,asset_license,imported_at) VALUES(?,?,?,?,?) "
                          "ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                          (pose["id"],json.dumps(pose,ensure_ascii=False),"yoga-api",
                           "Illustrations non redistribuées (Flaticon/CC0 : licences distinctes)",int(time.time())))


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 300_000)


def hash_token(token):
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def register_device(conn, group_id, device_id):
    token = secrets.token_urlsafe(36)
    conn.execute("INSERT INTO devices VALUES(?,?,?,?)",
                 (hash_token(token), group_id, device_id[:80], int(time.time())))
    return token


def create_group(password, device_id):
    if not isinstance(password, str) or len(password) < 12 or len(password) > 256:
        raise ValueError("Mot de passe : entre 12 et 256 caractères.")
    if not isinstance(device_id, str) or len(device_id) > 80:
        raise ValueError("Identifiant appareil invalide.")
    with LOCK, connection() as c:
        salt = secrets.token_bytes(24)
        group_id = secrets.token_hex(16)
        for _ in range(10):
            code = secrets.token_hex(5).upper()
            try:
                c.execute("INSERT INTO groups VALUES(?,?,?,?,?)",
                          (group_id, code, salt, password_hash(password, salt), int(time.time())))
                break
            except sqlite3.IntegrityError:
                pass
        else:
            raise RuntimeError("Impossible de générer un code.")
        token = register_device(c, group_id, device_id)
        initial = json.dumps({"schemaVersion": 1, "profiles": [], "activeProfileId": None})
        c.execute("INSERT INTO snapshots VALUES(?,?,?,?)",
                  (group_id, 0, initial, int(time.time())))
    return {"code": code, "token": token, "revision": 0}


def pair_group(code, password, device_id):
    if not isinstance(code, str) or not isinstance(password, str) or not isinstance(device_id, str):
        raise ValueError("Code et mot de passe requis.")
    with LOCK, connection() as c:
        row = c.execute("SELECT id,salt,password_hash FROM groups WHERE code=?",
                        (code.strip().upper(),)).fetchone()
        # Conserve une charge comparable en cas de code inconnu.
        salt = row[1] if row else b"x" * 24
        digest = password_hash(password[:256], salt)
        if not row or not hmac.compare_digest(digest, row[2]):
            raise PermissionError("Code ou mot de passe incorrect.")
        token = register_device(c, row[0], device_id)
        revision = c.execute("SELECT revision FROM snapshots WHERE group_id=?", (row[0],)).fetchone()[0]
    return {"code": code.strip().upper(), "token": token, "revision": revision}


def authenticated_group(headers):
    authorization = headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise PermissionError("Association requise.")
    token = authorization[7:]
    if len(token) > 200 or not token.isascii():
        raise PermissionError("Jeton invalide.")
    with connection() as c:
        row = c.execute("SELECT group_id FROM devices WHERE token_hash=?", (hash_token(token),)).fetchone()
        if not row:
            raise PermissionError("Appareil inconnu.")
        return row[0]


def current_snapshot(group_id):
    with connection() as c:
        row = c.execute("SELECT revision,payload FROM snapshots WHERE group_id=?", (group_id,)).fetchone()
    if not row:
        raise ValueError("Synchronisation introuvable.")
    return {"revision": row[0], "data": json.loads(row[1])}


def validate_snapshot(data):
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        raise ValueError("Format de sauvegarde non reconnu.")
    profiles = data.get("profiles")
    if not isinstance(profiles, list) or not 0 < len(profiles) <= 100:
        raise ValueError("Un à cent profils attendus.")
    seen = set()
    for p in profiles:
        if not isinstance(p, dict) or not isinstance(p.get("id"), str):
            raise ValueError("Profil invalide.")
        if len(p["id"]) > 120 or p["id"] in seen:
            raise ValueError("Identifiant de profil invalide.")
        seen.add(p["id"])
        if not isinstance(p.get("name"), str) or len(p["name"]) > 50:
            raise ValueError("Nom de profil invalide.")
        if not isinstance(p.get("history"), list) or len(p["history"]) > 2000:
            raise ValueError("Historique invalide.")
        if "credentials" in p:
            raise ValueError("Les identifiants secrets ne sont pas synchronisés.")
    if "credentials" in data:
        raise ValueError("Les identifiants secrets ne sont pas synchronisés.")
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def save_snapshot(group_id, expected_revision, data):
    payload = validate_snapshot(data)
    if len(payload.encode("utf-8")) > MAX_JSON:
        raise ValueError("Sauvegarde trop volumineuse.")
    with LOCK, connection() as c:
        revision = c.execute("SELECT revision FROM snapshots WHERE group_id=?", (group_id,)).fetchone()[0]
        if revision != expected_revision:
            return False, current_snapshot(group_id)
        revision += 1
        c.execute("UPDATE snapshots SET revision=?,payload=?,updated_at=? WHERE group_id=?",
                  (revision, payload, int(time.time()), group_id))
        return True, {"revision": revision}


def pose_library():
    with connection() as c:
        rows = c.execute("SELECT data FROM poses ORDER BY origin,id").fetchall()
    return {"poses": [json.loads(r[0]) for r in rows]}


def too_many_attempts(ip):
    now = time.monotonic()
    with LOCK:
        q = RATE[ip]
        while q and now - q[0] > 300:
            q.popleft()
        if len(q) >= 12:
            return True
        q.append(now)
        return False


def donation_destination():
    """Lien fourni par l'exploitant, jamais une destination de paiement inventée."""
    from urllib.parse import urlsplit
    url=os.environ.get("SICHOSANA_DONATION_URL","").strip()
    if not url or len(url)>1000:return None
    try:
        parsed=urlsplit(url)
        domain=(parsed.hostname or "").lower()
        accepted=domain in {"paypal.me","ko-fi.com","www.ko-fi.com","www.buymeacoffee.com","buymeacoffee.com"} or domain=="paypal.com" or domain.endswith(".paypal.com") or domain=="stripe.com" or domain.endswith(".stripe.com")
        if parsed.scheme!="https" or not accepted or parsed.username or parsed.password:
            return None
        return url
    except ValueError:
        return None


def original_art_status(root):
    """Statut réel des originaux. Aucun crédit tiers ne disparaît si un PNG manque."""
    import re
    try:
        manifest=json.loads((root / "data" / "original-art.json").read_text(encoding="utf-8"))
        files=manifest["files"]
        if not isinstance(files, list) or len(files)!=73 or len(set(files))!=73:
            return {"ready":False,"installed":0,"expected":73}
        path=root / "media" / "original"
        good=sum(1 for name in files if isinstance(name,str) and
                 re.fullmatch(r"[a-z0-9-]+",name) and
                 (path/(name+".png")).is_file() and (path/(name+".png")).stat().st_size>1000)
        return {"ready":good==73,"installed":good,"expected":73}
    except (OSError,ValueError,KeyError,TypeError):
        return {"ready":False,"installed":0,"expected":73}


class Handler(SimpleHTTPRequestHandler):
    server_version = "SichoSana/2.3"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def log_message(self, fmt, *args):
        LOGGER.info("%s %s", self.address_string(), fmt % args)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Permissions-Policy", "camera=(),microphone=(),geolocation=()")
        self.send_header("Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; media-src 'self'; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'")
        super().end_headers()

    def json_response(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body_json(self):
        length = int(self.headers.get("Content-Length") or "0")
        if not 0 < length <= MAX_JSON:
            raise ValueError("Requête vide ou trop volumineuse.")
        raw = self.rfile.read(length)
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Objet JSON attendu.")
        return data

    def serve_audio(self, url_path, head_only=False):
        """Réponses MP3 Range HTTP/1.1 compatibles iOS Safari et reprises audio."""
        from urllib.parse import unquote
        from pathlib import Path
        import re
        rel = unquote(url_path).lstrip("/")
        file_path = (STATIC / rel).resolve()
        if not file_path.is_relative_to(STATIC) or not file_path.is_file():
            self.send_error(404, "Audio introuvable.")
            return
        size = file_path.stat().st_size
        if not size:
            self.send_error(404, "Audio vide.")
            return
        value = self.headers.get("Range", "")
        start, end = 0, size - 1
        partial = False
        if value:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", value.strip())
            if not match or not (match.group(1) or match.group(2)):
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            first, last = match.groups()
            if first:
                start = int(first)
                end = min(int(last), size - 1) if last else size - 1
            else:
                length = int(last)
                start = max(0, size - length)
            if start >= size or start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            partial = True
        self.send_response(206 if partial else 200)
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Cache-Control", "public, max-age=86400")
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if head_only:
            return
        with file_path.open("rb") as src:
            src.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                data = src.read(min(64_000, remaining))
                if not data:
                    break
                self.wfile.write(data)
                remaining -= len(data)

    def do_HEAD(self):
        path = urlsplit(self.path).path
        if path.startswith("/voice/") and path.endswith(".mp3"):
            return self.serve_audio(path, head_only=True)
        return super().do_HEAD()

    def do_GET(self):
        path = urlsplit(self.path).path
        try:
            if accounts.api(self, 'GET', path, connection):
                return
            if path == "/api/v1/content/horoscope":
                params=parse_qs(urlsplit(self.path).query)
                return self.json_response(200, astrology.daily(params.get('sign',[''])[0], params.get('period',['daily'])[0]))
            if path == "/api/health":
                return self.json_response(200, {"status": "ok", "storage": "sqlite", "version": "2.3.0"})
            if path == "/api/v1/public-config":
                return self.json_response(200, {"donationUrl": donation_destination()})
            if path == "/api/v1/media/original-status":
                return self.json_response(200, original_art_status(STATIC))
            if path == "/api/v1/poses":
                return self.json_response(200, pose_library())
            if path == "/api/v1/snapshot":
                return self.json_response(200, current_snapshot(authenticated_group(self.headers)))
            if path.startswith("/api/"):
                return self.json_response(404, {"error": "Route inexistante."})
            if path.startswith("/voice/") and path.endswith(".mp3"):
                return self.serve_audio(path)
            if path == "/":
                self.path = "/index.html"
            return super().do_GET()
        except PermissionError as exc:
            return self.json_response(401, {"error": str(exc)})
        except (ValueError, json.JSONDecodeError) as exc:
            return self.json_response(400, {"error": str(exc)})
        except Exception:
            LOGGER.exception("GET failed")
            return self.json_response(500, {"error": "Erreur interne."})

    def do_POST(self):
        path = urlsplit(self.path).path
        try:
            if path.startswith('/api/v1/auth/') and too_many_attempts(self.client_address[0]):
                return self.json_response(429, {'error': 'Trop de tentatives. Réessaye dans quelques minutes.'})
            if accounts.api(self, 'POST', path, connection):
                return
            if path not in ("/api/v1/groups", "/api/v1/pair"):
                return self.json_response(404, {"error": "Route inexistante."})
            if too_many_attempts(self.client_address[0]):
                return self.json_response(429, {"error": "Trop de tentatives. Réessayer dans quelques minutes."})
            data = self.body_json()
            if path == "/api/v1/groups":
                out = create_group(data.get("password"), data.get("deviceId", ""))
            else:
                out = pair_group(data.get("code"), data.get("password"), data.get("deviceId", ""))
            return self.json_response(201, out)
        except PermissionError as exc:
            return self.json_response(403, {"error": str(exc)})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self.json_response(400, {"error": str(exc)})
        except Exception:
            LOGGER.exception("POST failed")
            return self.json_response(500, {"error": "Erreur interne."})

    def do_PUT(self):
        if urlsplit(self.path).path not in ('/api/v1/snapshot','/api/v1/account/snapshot'):
            return self.json_response(404, {"error": "Route inexistante."})
        try:
            if accounts.api(self, 'PUT', urlsplit(self.path).path, connection):
                return
            group_id = authenticated_group(self.headers)
            raw = self.headers.get("If-Match", "-1")
            if not raw.isdigit():
                raise ValueError("Numéro de révision If-Match requis.")
            expected_revision = int(raw)
            body = self.body_json()
            ok, out = save_snapshot(group_id, expected_revision, body.get("data"))
            return self.json_response(200 if ok else 409, out)
        except PermissionError as exc:
            return self.json_response(401, {"error": str(exc)})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self.json_response(400, {"error": str(exc)})
        except Exception:
            LOGGER.exception("PUT failed")
            return self.json_response(500, {"error": "Erreur interne."})


    def do_PATCH(self):
        path = urlsplit(self.path).path
        if accounts.api(self, 'PATCH', path, connection):
            return
        return self.json_response(404, {'error': 'Route inexistante.'})


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    initialize()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    stop_emails = threading.Event()

    def deliver_emails_forever():
        while not stop_emails.wait(75):
            try:
                accounts.deliver_pending(connection)
            except Exception:
                LOGGER.exception("Echec de livraison des emails en attente")

    mail_thread = threading.Thread(target=deliver_emails_forever,
                                   name="sichosana-mail-outbox", daemon=True)
    mail_thread.start()
    LOGGER.info("SichoSana ready at %s:%s, SQLite %s", HOST, PORT, DB_PATH)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_emails.set()
        server.server_close()


if __name__ == "__main__":
    main()
