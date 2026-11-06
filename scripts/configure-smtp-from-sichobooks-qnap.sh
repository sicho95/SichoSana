#!/bin/sh
# Réutiliser les variables SMTP du seul worker SichoBooks.
# Ne modifie que .env et le conteneur SichoSana (pas SichoBooks).
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
SOURCE="sichobooks-worker-1"
docker inspect "$SOURCE" >/dev/null 2>&1 || {
  echo "SichoBooks worker non détecté : arrêt sans modification."
  exit 1
}
echo "[SichoSana] Reprise du SMTP depuis $SOURCE sans afficher les secrets..."
docker inspect "$SOURCE" | docker run --rm --network bridge -i \
  -v "$ROOT:/workspace" -w /workspace python:3.12-slim \
  python scripts/adopt-sichobooks-smtp.py
docker compose -f compose.yaml -p sichosana config --quiet
docker compose -f compose.yaml -p sichosana up -d --no-deps --force-recreate
echo "[SichoSana] Vérification de l'authentification SMTP depuis son propre conteneur..."
docker exec -i sichosana-app python - <<'PY'
import os
import smtplib
import ssl

host=os.environ["SICHOSANA_SMTP_HOST"]
port=int(os.environ["SICHOSANA_SMTP_PORT"])
user=os.environ["SICHOSANA_SMTP_USER"]
password=os.environ["SICHOSANA_SMTP_PASSWORD"]
security=os.environ.get("SICHOSANA_SMTP_SECURITY","ssl")
try:
    if security=="ssl":
        server=smtplib.SMTP_SSL(host,port,timeout=15,context=ssl.create_default_context())
    elif security=="starttls":
        server=smtplib.SMTP(host,port,timeout=15)
    else:
        raise ValueError("Connexion sans chiffrement interdite.")
    with server:
        if security=="starttls":
            server.starttls(context=ssl.create_default_context())
        server.login(user,password)
    print("SMTP_AUTH_OK : Gmail accepte les identifiants, aucun message de test envoyé.")
except (OSError, smtplib.SMTPException, ValueError) as exc:
    print("SMTP_AUTH_ECHEC :",type(exc).__name__)
    raise SystemExit(1)
PY
echo "[SichoSana] Paramètres SMTP repris. Vérifier ensuite le parcours d'inscription."
