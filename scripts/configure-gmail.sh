#!/bin/sh
# SichoSana: configuration SMTP Gmail locale, sans copier de secret dans Git ni dans les commandes.
# Sur le NAS: sh scripts/configure-gmail.sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
umask 077
if [ ! -f .env ]; then
  [ -f .env.example ] || { echo "Fichier .env.example absent." >&2; exit 1; }
  cp .env.example .env
fi
printf '%s\n' 'SichoSana — Gmail provisoire (aucune modification Cloudflare)'
printf 'Adresse expéditrice [sicho95@gmail.com] : '
IFS= read -r ADDRESS
[ -n "$ADDRESS" ] || ADDRESS="sicho95@gmail.com"
case "$ADDRESS" in
  *[!A-Za-z0-9._%+@-]*|\'\') echo "Adresse invalide." >&2; exit 1 ;;
esac
case "$ADDRESS" in *@*.*) : ;; *) echo "Adresse invalide." >&2; exit 1 ;; esac
printf '%s\n' 'Utilise un mot de passe d’application Google (validation en 2 étapes requise).'
printf '%s' 'Mot de passe d’application (saisie masquée) : '
oldstty="$(stty -g 2>/dev/null || true)"
restore_tty(){ [ -z "$oldstty" ] || stty "$oldstty" 2>/dev/null || true; }
trap 'restore_tty' EXIT HUP INT TERM
stty -echo
IFS= read -r PASSWORD
restore_tty
printf '\n'
PASSWORD="$(printf '%s' "$PASSWORD" | tr -d '[:space:]')"
case "$PASSWORD" in
  *[!A-Za-z0-9]*|'') echo "Mot de passe d’application invalide." >&2; exit 1 ;;
esac
[ "${#PASSWORD}" -ge 16 ] || { echo "Le code doit comporter 16 caractères." >&2; exit 1; }
TMP="$(mktemp "$ROOT/.env.mail.XXXXXX")"
trap 'rm -f "$TMP"; restore_tty' EXIT HUP INT TERM
sed '/^SICHOSANA_SMTP_/d' .env > "$TMP"
{
  printf '\nSICHOSANA_SMTP_HOST=smtp.gmail.com\n'
  printf 'SICHOSANA_SMTP_PORT=465\n'
  printf 'SICHOSANA_SMTP_SECURITY=ssl\n'
  printf 'SICHOSANA_SMTP_FROM=%s\n' "$ADDRESS"
  printf 'SICHOSANA_SMTP_USER=%s\n' "$ADDRESS"
  printf 'SICHOSANA_SMTP_PASSWORD=%s\n' "$PASSWORD"
} >> "$TMP"
chmod 600 "$TMP"
mv "$TMP" .env
unset PASSWORD
echo 'Configuration Gmail sauvegardée localement (.env, chmod 600).'
echo 'Pour appliquer :'
if [ -f compose.bridge.yaml ]; then
  echo 'docker compose -f compose.yaml -f compose.bridge.yaml -p sichosana up -d --no-deps --force-recreate'
elif [ -f compose.cloudflare.yaml ]; then
  echo 'docker compose -f compose.yaml -f compose.cloudflare.yaml -p sichosana up -d --no-deps --force-recreate'
else
  echo 'docker compose -f compose.yaml -p sichosana up -d --no-deps --force-recreate'
fi
echo 'Ne jamais transmettre le mot de passe d’application à ChatGPT.'
