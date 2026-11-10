#!/bin/sh
# SichoSana — configuration Gmail SMTP uniquement sur NAS-DAMIEN.
# Secret local dans .env (mode 0600), jamais GitHub ni sorties de terminal.
set -eu
BASE="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$BASE"
[ -f compose.yaml ] || { echo "Projet SichoSana introuvable."; exit 1; }
[ -f .env ] || cp .env.example .env
chmod 600 .env

printf 'Adresse Gmail expéditrice [sicho95@gmail.com] : '
IFS= read -r MAIL_ADDR
MAIL_ADDR="${MAIL_ADDR:-sicho95@gmail.com}"
case "$MAIL_ADDR" in
  *[!a-zA-Z0-9@._+%-]*|'') echo "Adresse contenant des caractères non autorisés."; exit 1 ;;
esac
case "$MAIL_ADDR" in *@*.*) ;; *) echo "Adresse invalide."; exit 1;; esac

echo "Google exige un mot de passe d'application (16 caractères),"
echo "avec validation en deux étapes, et non le mot de passe Google habituel."
printf "Mot de passe d'application (saisie masquée) : "
stty -echo
trap 'stty echo 2>/dev/null || true' EXIT HUP INT TERM
IFS= read -r SECRET
stty echo
printf '\n'
SECRET="$(printf '%s' "$SECRET" | tr -d '[:space:]')"
case "$SECRET" in *[!a-zA-Z0-9]*|'') echo "Mot de passe d'application invalide."; exit 1;; esac
if [ "${#SECRET}" -ne 16 ]; then
  echo "Le mot de passe d'application doit contenir exactement 16 caractères."
  exit 1
fi

cp -p .env ".env.bak.$(date +%Y%m%d%H%M%S)"
TMP="$(mktemp "./.smtp.XXXXXXXX")"
trap 'stty echo 2>/dev/null || true; rm -f "$TMP"' EXIT HUP INT TERM
chmod 600 "$TMP"
grep -v '^SICHOSANA_SMTP_' .env > "$TMP" || true
cat >> "$TMP" <<EOF
SICHOSANA_SMTP_HOST=smtp.gmail.com
SICHOSANA_SMTP_PORT=465
SICHOSANA_SMTP_SECURITY=ssl
SICHOSANA_SMTP_USER=$MAIL_ADDR
SICHOSANA_SMTP_PASSWORD=$SECRET
SICHOSANA_SMTP_FROM=$MAIL_ADDR
EOF
mv "$TMP" .env
chmod 600 .env
unset SECRET
docker compose -f compose.yaml -p sichosana config -q
docker compose -f compose.yaml -p sichosana up -d --no-deps --force-recreate
echo "Test connexion SMTP Gmail :"
docker exec -i sichosana-app python -c '
import os,smtplib,ssl
try:
    with smtplib.SMTP_SSL("smtp.gmail.com",465,timeout=15,context=ssl.create_default_context()) as smtp:
        smtp.login(os.environ["SICHOSANA_SMTP_USER"],os.environ["SICHOSANA_SMTP_PASSWORD"])
    print("SMTP_GMAIL_LOGIN_OK : authentification valide, aucun email de test envoyé.")
except Exception as exc:
    print("SMTP_GMAIL_LOGIN_ECHEC :",type(exc).__name__)
    raise SystemExit(1)
'
echo "Tu pourras relancer ce même script lors du changement d'adresse."
