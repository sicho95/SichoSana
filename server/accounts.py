"""SichoSana V2: authentification, comptes en attente, validation admin et e-mails.

Les codes et secrets ne sont jamais déposés dans Git. L'inscription publique est
indisponible tant que SMTP n'est pas configuré. Tous les jetons sont hachés en base.
"""
from __future__ import annotations

from datetime import datetime, timezone
from email.message import EmailMessage
from html import escape
import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import sqlite3
import ssl
import time
import unicodedata
from urllib.parse import quote

SESSION_TTL = 30 * 86400
RESET_TTL = 1800
MAX_PROFILE_DATA = 1_200_000
HANDLE_RE = re.compile(r"^[\w.-]{3,30}$", re.UNICODE)
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,180}\.[^@\s]{2,}$")
ALLOWED_CHANGES = {"approve", "suspend", "restore", "promote", "demote", "delete"}
WELCOME = ("Bienvenue dans l’univers SichoSana. "
           "Ici, chaque respiration ouvre un espace pour ralentir, "
           "te retrouver et t’offrir un instant rien qu’à toi.")


class AccountError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def now():
    return int(time.time())


def norm_handle(value):
    if not isinstance(value, str):
        raise AccountError(400, "Pseudo requis.")
    value = unicodedata.normalize("NFKC", value).strip()
    if not HANDLE_RE.fullmatch(value):
        raise AccountError(400, "Pseudo de 3 à 30 caractères (lettres, chiffres, _ . -).")
    return value, value.casefold()


def norm_email(value):
    if not isinstance(value, str) or not EMAIL_RE.fullmatch(value.strip()):
        raise AccountError(400, "Adresse email invalide.")
    value = value.strip()
    return value, value.casefold()


def check_password(value, bootstrap=False):
    if not isinstance(value, str) or len(value) > 256:
        raise AccountError(400, "Mot de passe invalide.")
    if not bootstrap and len(value) < 10:
        raise AccountError(400, "Choisis au moins 10 caractères pour ton mot de passe.")
    if not bootstrap and value.lower() in {"1234567890", "motdepasse", "password123", "123456789a"}:
        raise AccountError(400, "Choisis un mot de passe moins courant.")
    if not value:
        raise AccountError(400, "Mot de passe requis.")


def password_digest(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 450_000)


def tokhash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def init_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            handle TEXT NOT NULL,
            handle_key TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            email_key TEXT NOT NULL UNIQUE,
            password_salt BLOB NOT NULL,
            password_hash BLOB NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user','admin')),
            status TEXT NOT NULL CHECK(status IN ('pending','active','suspended')),
            must_change INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            approved_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS account_sessions (
            token_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS password_resets (
            token_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            used_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS account_snapshots (
            user_id TEXT PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,
            revision INTEGER NOT NULL DEFAULT 0,
            payload TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS email_outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            kind TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            sent_at INTEGER,
            failure TEXT
        );
    """)


def public_user(row):
    return {
        "id": row["id"],
        "pseudo": row["handle"],
        "email": row["email"],
        "role": row["role"],
        "status": row["status"],
        "mustChangePassword": bool(row["must_change"]),
        "createdAt": row["created_at"],
    }


def get_account(conn, account_id):
    return conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()


def create_admin(conn, handle, email, password):
    """Bootstrap explicite sur NAS, une seule fois, via CLI avec mot de passe lu sans écho."""
    handle, handle_key = norm_handle(handle)
    email, email_key = norm_email(email)
    check_password(password, bootstrap=True)
    if conn.execute("SELECT 1 FROM accounts WHERE role='admin' LIMIT 1").fetchone():
        raise AccountError(409, "Un administrateur existe déjà : utilise le panneau d'administration.")
    user_id = secrets.token_hex(16)
    salt = secrets.token_bytes(24)
    conn.execute(
        "INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (user_id, handle, handle_key, email, email_key, salt,
         password_digest(password, salt), "admin", "active", 1, now(), now())
    )
    return user_id


def smtp_ready():
    if os.environ.get("SICHOSANA_TEST_MODE") == "1" and os.environ.get("SICHOSANA_HOST") == "127.0.0.1":
        return True
    return all(os.environ.get(k) for k in ("SICHOSANA_SMTP_HOST", "SICHOSANA_SMTP_FROM",
                                          "SICHOSANA_PUBLIC_URL"))


def enqueue(conn, address, subject, body, kind):
    conn.execute("INSERT INTO email_outbox(recipient,subject,body,kind,created_at) VALUES (?,?,?,?,?)",
                 (address, subject, body, kind, now()))


def deliver_pending(connection_factory):
    """Livraison best effort : la file SQLite survit aux indisponibilités SMTP."""
    if not smtp_ready() or (
        os.environ.get("SICHOSANA_TEST_MODE") == "1" and os.environ.get("SICHOSANA_HOST") == "127.0.0.1"
    ):
        return
    host = os.environ["SICHOSANA_SMTP_HOST"]
    port = int(os.environ.get("SICHOSANA_SMTP_PORT", "465"))
    sender = os.environ["SICHOSANA_SMTP_FROM"]
    username = os.environ.get("SICHOSANA_SMTP_USER", "")
    password = os.environ.get("SICHOSANA_SMTP_PASSWORD", "")
    mode = os.environ.get("SICHOSANA_SMTP_SECURITY", "ssl").lower()
    with connection_factory() as conn:
        rows = conn.execute("SELECT id,recipient,subject,body FROM email_outbox "
                            "WHERE sent_at IS NULL ORDER BY id LIMIT 15").fetchall()
    for row in rows:
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = row["recipient"]
        msg["Subject"] = row["subject"]
        msg.set_content(row["body"])
        page = '<!doctype html><html lang="fr"><body style="margin:0;background:#f6f3eb;font-family:Arial,sans-serif;color:#374a40"><div style="max-width:560px;margin:30px auto;padding:36px;background:white;border-radius:20px"><h1 style="color:#718d76">SichoSana</h1><p style="white-space:pre-line;line-height:1.7">' + escape(row["body"]) + '</p><p style="font-size:13px;color:#687b70">L’équipe de SichoSana</p></div></body></html>'
        msg.add_alternative(page, subtype="html")
        try:
            if mode == "ssl":
                server = smtplib.SMTP_SSL(host, port, timeout=12, context=ssl.create_default_context())
            else:
                server = smtplib.SMTP(host, port, timeout=12)
            with server:
                if mode == "starttls":
                    server.starttls(context=ssl.create_default_context())
                if username:
                    server.login(username, password)
                server.send_message(msg)
            with connection_factory() as conn:
                conn.execute("UPDATE email_outbox SET sent_at=?, failure=NULL WHERE id=?", (now(), row["id"]))
        except (OSError, smtplib.SMTPException) as exc:
            with connection_factory() as conn:
                conn.execute("UPDATE email_outbox SET failure=? WHERE id=?",
                             (type(exc).__name__, row["id"]))
            break


def bearer_user(conn, headers, require_admin=False, allow_forced_change=False):
    auth = headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else ""
    if not token or len(token) > 180 or not token.isascii():
        raise AccountError(401, "Connecte-toi pour continuer.")
    row = conn.execute(
        "SELECT a.* FROM account_sessions s JOIN accounts a ON a.id=s.user_id "
        "WHERE s.token_hash=? AND s.expires_at>?", (tokhash(token), now())
    ).fetchone()
    if row is None:
        raise AccountError(401, "Session expirée, reconnecte-toi.")
    if row["status"] != "active":
        raise AccountError(403, "Compte non actif.")
    if row["must_change"] and not allow_forced_change:
        raise AccountError(403, "Change ton mot de passe provisoire pour continuer.")
    if require_admin and row["role"] != "admin":
        raise AccountError(403, "Accès réservé aux administrateurs.")
    return row


def issue_session(conn, user_id):
    token = secrets.token_urlsafe(42)
    conn.execute("INSERT INTO account_sessions VALUES (?,?,?,?)",
                 (tokhash(token), user_id, now(), now() + SESSION_TTL))
    return token


def new_account(conn, payload):
    handle, key = norm_handle(payload.get("pseudo"))
    email, email_key = norm_email(payload.get("email"))
    password = payload.get("password")
    check_password(password)
    user_id = secrets.token_hex(16)
    salt = secrets.token_bytes(24)
    try:
        conn.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                     (user_id, handle, key, email, email_key, salt,
                      password_digest(password, salt), "user", "pending", 0, now(), None))
    except sqlite3.IntegrityError as exc:
        if conn.execute("SELECT 1 FROM accounts WHERE handle_key=?", (key,)).fetchone():
            raise AccountError(409, "Ce pseudo est déjà utilisé.") from exc
        raise AccountError(409, "Cette adresse email est déjà associée à un compte.") from exc
    admins = conn.execute("SELECT email FROM accounts WHERE role='admin' AND status='active'").fetchall()
    url = os.environ.get("SICHOSANA_PUBLIC_URL", "").rstrip("/")
    for admin in admins:
        enqueue(conn, admin["email"], "SichoSana — inscription à valider",
                f"Une demande d’inscription vient d’arriver.\n\nPseudo : {handle}\n"
                f"Email : {email}\n\nOuvre ton panneau d’administration : {url}\n\nL’équipe de SichoSana",
                "registration")
    enqueue(conn, email, "SichoSana — inscription reçue",
            f"Bonjour {handle},\n\nTa demande d’inscription est bien arrivée.\n"
            "Un membre de l’équipe validera prochainement ton accès.\n\n"
            "À bientôt pour un moment rien qu’à toi.\n\nL’équipe de SichoSana",
            "registration_pending")
    return {"status": "pending", "message": "Inscription reçue. Un administrateur doit valider ton compte."}


def login(conn, payload):
    _, key = norm_handle(payload.get("pseudo"))
    password = payload.get("password")
    if not isinstance(password, str):
        raise AccountError(400, "Mot de passe requis.")
    row = conn.execute("SELECT * FROM accounts WHERE handle_key=?", (key,)).fetchone()
    salt = row["password_salt"] if row else b"\0" * 24
    digest = password_digest(password[:256], salt)
    if not row or not hmac.compare_digest(digest, row["password_hash"]):
        raise AccountError(401, "Pseudo ou mot de passe incorrect.")
    if row["status"] == "pending":
        raise AccountError(403, "Compte en attente de validation par un administrateur.")
    if row["status"] == "suspended":
        raise AccountError(403, "Ce compte est suspendu.")
    conn.execute("DELETE FROM account_sessions WHERE user_id=? AND expires_at<?", (row["id"], now()))
    return {"token": issue_session(conn, row["id"]), "user": public_user(row)}


def new_password(conn, actor, payload):
    old = payload.get("currentPassword")
    password = payload.get("newPassword")
    check_password(password)
    if not isinstance(old, str) or not hmac.compare_digest(
        password_digest(old[:256], actor["password_salt"]), actor["password_hash"]
    ):
        raise AccountError(403, "Mot de passe actuel incorrect.")
    if old == password:
        raise AccountError(400, "Choisis un mot de passe différent.")
    salt = secrets.token_bytes(24)
    conn.execute("UPDATE accounts SET password_salt=?,password_hash=?,must_change=0 WHERE id=?",
                 (salt, password_digest(password, salt), actor["id"]))
    # Le jeton courant reste valable pour permettre la reprise immédiate ;
    # les autres sessions sont révoquées par l'appelant.
    return {"message": "Mot de passe modifié.", "mustChangePassword": False}


def request_reset(conn, payload):
    value = str(payload.get("pseudoOrEmail", "")).strip()
    if not value or len(value) > 254:
        raise AccountError(400, "Pseudo ou adresse email requis.")
    key = unicodedata.normalize("NFKC", value).casefold()
    account = conn.execute("SELECT * FROM accounts WHERE handle_key=? OR email_key=?",
                           (key, key)).fetchone()
    if account and account["status"] == "active":
        token = secrets.token_urlsafe(36)
        conn.execute("DELETE FROM password_resets WHERE user_id=?", (account["id"],))
        conn.execute("INSERT INTO password_resets VALUES (?,?,?,?,NULL)",
                     (tokhash(token), account["id"], now(), now() + RESET_TTL))
        url = os.environ.get("SICHOSANA_PUBLIC_URL", "").rstrip("/")
        enqueue(conn, account["email"], "SichoSana — réinitialiser ton mot de passe",
                f"Bonjour {account['handle']},\n\nPour définir un nouveau mot de passe, ouvre ce lien "
                f"(valable 30 minutes, à usage unique) :\n{url}/?reset={quote(token)}\n\n"
                "Si tu n’as pas demandé cela, ignore simplement ce message.\n\nL’équipe de SichoSana",
                "password_reset")
    return {"message": "Si un compte actif correspond, un email de réinitialisation sera envoyé."}


def reset_password(conn, payload):
    token = payload.get("token")
    password = payload.get("newPassword")
    check_password(password)
    if not isinstance(token, str) or len(token) > 180:
        raise AccountError(400, "Lien de réinitialisation invalide.")
    row = conn.execute("SELECT r.user_id FROM password_resets r JOIN accounts a ON a.id=r.user_id "
                       "WHERE r.token_hash=? AND r.expires_at>? AND r.used_at IS NULL "
                       "AND a.status='active'", (tokhash(token), now())).fetchone()
    if not row:
        raise AccountError(400, "Ce lien a expiré ou a déjà été utilisé.")
    salt = secrets.token_bytes(24)
    conn.execute("UPDATE accounts SET password_salt=?,password_hash=?,must_change=0 WHERE id=?",
                 (salt, password_digest(password, salt), row["user_id"]))
    conn.execute("UPDATE password_resets SET used_at=? WHERE token_hash=?", (now(), tokhash(token)))
    conn.execute("DELETE FROM account_sessions WHERE user_id=?", (row["user_id"],))
    return {"message": "Mot de passe changé. Tu peux te connecter."}


def manage(conn, actor, user_id, action):
    if action not in ALLOWED_CHANGES:
        raise AccountError(400, "Action inconnue.")
    target = get_account(conn, user_id)
    if not target:
        raise AccountError(404, "Compte introuvable.")
    if target["id"] == actor["id"] and action in ("suspend", "demote", "delete"):
        raise AccountError(409, "Impossible de retirer tes propres droits ou de supprimer ton compte admin.")
    if action in ("demote", "delete", "suspend") and target["role"] == "admin":
        count = conn.execute("SELECT COUNT(*) FROM accounts WHERE role='admin' AND status='active'").fetchone()[0]
        if count <= 1 and target["status"] == "active":
            raise AccountError(409, "Le dernier administrateur actif doit être conservé.")
    if action == "delete":
        conn.execute("DELETE FROM account_sessions WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM password_resets WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM account_snapshots WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM accounts WHERE id=?", (user_id,))
        return {"deleted": True}
    if action == "approve":
        if target["status"] != "pending":
            raise AccountError(409, "Ce compte n'est pas en attente.")
        conn.execute("UPDATE accounts SET status='active',approved_at=? WHERE id=?", (now(), user_id))
        enqueue(conn, target["email"], "Bienvenue dans SichoSana",
                f"Bonjour {target['handle']},\n\nTon inscription vient d’être validée !\n\n"
                f"{WELCOME}\n\nTon espace est prêt : "
                f"{os.environ.get('SICHOSANA_PUBLIC_URL', 'https://yoga.sicho.cc.cd')}\n\n"
                "Au plaisir de partager avec toi ces instants de sérénité.\n\nL’équipe de SichoSana",
                "welcome")
    elif action == "suspend":
        conn.execute("UPDATE accounts SET status='suspended' WHERE id=?", (user_id,))
        conn.execute("DELETE FROM account_sessions WHERE user_id=?", (user_id,))
    elif action == "restore":
        if target["status"] != "suspended":
            raise AccountError(409, "Compte non suspendu.")
        conn.execute("UPDATE accounts SET status='active' WHERE id=?", (user_id,))
    elif action in ("promote", "demote"):
        if target["status"] != "active":
            raise AccountError(409, "Valide le compte avant de modifier ses droits.")
        conn.execute("UPDATE accounts SET role=? WHERE id=?",
                     ("admin" if action == "promote" else "user", user_id))
    return public_user(get_account(conn, user_id))


def snapshot(conn, user_id):
    row = conn.execute("SELECT revision,payload FROM account_snapshots WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        return {"revision": 0, "data": None}
    return {"revision": row["revision"], "data": json.loads(row["payload"])}


def save_snapshot(conn, user_id, rev, data):
    from server.app import validate_snapshot  # le format historique reste compatible
    serialized = validate_snapshot(data)
    if len(serialized.encode("utf-8")) > MAX_PROFILE_DATA:
        raise AccountError(413, "Sauvegarde trop volumineuse.")
    row = snapshot(conn, user_id)
    if row["revision"] != rev:
        raise AccountError(409, json.dumps(row, ensure_ascii=False))
    if row["revision"] == 0:
        conn.execute("INSERT INTO account_snapshots VALUES (?,?,?,?)",
                     (user_id, 1, serialized, now()))
    else:
        conn.execute("UPDATE account_snapshots SET revision=revision+1,payload=?,updated_at=? WHERE user_id=?",
                     (serialized, now(), user_id))
    return {"revision": rev + 1}


def api(handler, method, path, connection_factory):
    """Renvoie True si la route /api/v1 V2 a été prise en charge."""
    public = {
        ("GET", "/api/v1/auth/config"),
        ("POST", "/api/v1/auth/register"), ("POST", "/api/v1/auth/login"),
        ("POST", "/api/v1/auth/forgot"), ("POST", "/api/v1/auth/reset"),
    }
    private = {
        ("GET", "/api/v1/auth/me"), ("POST", "/api/v1/auth/logout"),
        ("POST", "/api/v1/auth/password"),
        ("GET", "/api/v1/account/snapshot"), ("PUT", "/api/v1/account/snapshot"),
        ("GET", "/api/v1/admin/users"), ("POST", "/api/v1/admin/emails/retry"),
    }
    is_admin_path = path.startswith("/api/v1/admin/users/") and method == "PATCH"
    if (method, path) not in public | private and not is_admin_path:
        return False
    try:
        if path == "/api/v1/auth/config":
            with connection_factory() as cx:
                admin_exists=bool(cx.execute("SELECT 1 FROM accounts WHERE role='admin' AND status='active' LIMIT 1").fetchone())
            handler.json_response(200, {"registrationOpen": smtp_ready() and admin_exists,
                                        "emailConfigured": smtp_ready(), "adminReady": admin_exists})
            return True
        with connection_factory() as conn:
            if (method, path) in public:
                if method == "POST":
                    payload = handler.body_json()
                    if path == "/api/v1/auth/register":
                        if not smtp_ready():
                            raise AccountError(503, "Inscriptions indisponibles tant que l'envoi d'emails n'est pas configuré.")
                        if not conn.execute("SELECT 1 FROM accounts WHERE role='admin' AND status='active' LIMIT 1").fetchone():
                            raise AccountError(503, "Les inscriptions ouvriront dès l'activation du compte administrateur.")
                        code, result = 201, new_account(conn, payload)
                    elif path == "/api/v1/auth/login":
                        code, result = 200, login(conn, payload)
                    elif path == "/api/v1/auth/forgot":
                        if not smtp_ready():
                            raise AccountError(503, "Récupération indisponible : email non configuré.")
                        code, result = 200, request_reset(conn, payload)
                    else:
                        code, result = 200, reset_password(conn, payload)
                else:
                    code, result = 200, {}
            else:
                forced_ok = path in ("/api/v1/auth/me", "/api/v1/auth/password", "/api/v1/auth/logout")
                admin = path.startswith("/api/v1/admin/")
                actor = bearer_user(conn, handler.headers, require_admin=admin,
                                    allow_forced_change=forced_ok)
                if path == "/api/v1/auth/me":
                    code, result = 200, {"user": public_user(actor)}
                elif path == "/api/v1/auth/logout":
                    token = handler.headers.get("Authorization", "")[7:]
                    conn.execute("DELETE FROM account_sessions WHERE token_hash=?", (tokhash(token),))
                    code, result = 200, {"message": "Déconnecté."}
                elif path == "/api/v1/auth/password":
                    result = new_password(conn, actor, handler.body_json())
                    token = handler.headers.get("Authorization", "")[7:]
                    conn.execute("DELETE FROM account_sessions WHERE user_id=? AND token_hash!=?",
                                 (actor["id"], tokhash(token)))
                    code = 200
                elif path == "/api/v1/account/snapshot":
                    if method == "GET":
                        code, result = 200, snapshot(conn, actor["id"])
                    else:
                        raw = handler.headers.get("If-Match", "")
                        if not raw.isdigit():
                            raise AccountError(400, "Révision If-Match obligatoire.")
                        try:
                            result = save_snapshot(conn, actor["id"], int(raw),
                                                   handler.body_json().get("data"))
                        except AccountError as ex:
                            if ex.status != 409:
                                raise
                            code, result = 409, json.loads(str(ex))
                        else:
                            code = 200
                elif path == "/api/v1/admin/users":
                    rows = conn.execute("SELECT * FROM accounts ORDER BY created_at DESC").fetchall()
                    code, result = 200, {"users": [public_user(row) for row in rows]}
                elif path == "/api/v1/admin/emails/retry":
                    code, result = 200, {"message": "Une nouvelle tentative d'envoi a été demandée."}
                elif is_admin_path:
                    target = path.rsplit("/", 1)[-1]
                    code, result = 200, manage(conn, actor, target, handler.body_json().get("action"))
        # L'envoi est réalisé après commit ; une erreur SMTP n'annule jamais une validation.
        if method == "POST" and path in ("/api/v1/auth/register", "/api/v1/auth/forgot", "/api/v1/admin/emails/retry") or is_admin_path:
            deliver_pending(connection_factory)
        handler.json_response(code, result)
    except AccountError as exc:
        handler.json_response(exc.status, {"error": str(exc)})
    except (ValueError, TypeError, sqlite3.IntegrityError, json.JSONDecodeError):
        handler.json_response(400, {"error": "Requête invalide."})
    return True
