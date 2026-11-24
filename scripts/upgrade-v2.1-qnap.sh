#!/bin/sh
# SichoSana — montée de version NAS non destructive.
# Ni les routes Cloudflare, ni Tailscale, ni les autres conteneurs ne sont modifiés.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
BRANCH="dev/sichosana-20261105"
echo "[SichoSana] Dossier : $ROOT"
command -v git >/dev/null || { echo "Git absent"; exit 1; }
docker compose version >/dev/null || { echo "Docker Compose absent"; exit 1; }
test "$(git branch --show-current)" = "$BRANCH" || { echo "Branche inattendue : arrêter."; exit 1; }
# Autoriser seulement les overrides non versionnés d'une ancienne installation.
DIRTY="$(git status --porcelain | grep -v '^?? compose.bridge.yaml$' | grep -v '^?? compose.cloudflare.yaml$' || true)"
[ -z "$DIRTY" ] || { echo "Modifications locales : sauvegarder avant upgrade."; printf '%s\n' "$DIRTY"; exit 1; }
[ -f .env ] || cp .env.example .env
chmod 600 .env

echo "[SichoSana] Sauvegarde SQLite cohérente avant changement."
docker exec -i sichosana-app python - <<'PY'
import sqlite3,datetime
from pathlib import Path
source=Path('/data/sichosana.sqlite3')
if not source.is_file():
    raise SystemExit('Base SQLite introuvable : arrêt pour protéger les comptes.')
backup=source.parent/'backups'
backup.mkdir(mode=0o700,exist_ok=True)
target=backup/('sichosana-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.sqlite3')
with sqlite3.connect(str(source)) as db, sqlite3.connect(str(target)) as copy:
    db.backup(copy)
print('BACKUP_SQLITE_OK',target.name)
PY

echo "[SichoSana] Mise à jour contrôlée GitHub : $BRANCH"
git fetch --no-tags origin "$BRANCH"
git merge --ff-only FETCH_HEAD
echo "[SichoSana] Préparer images PNG Yoga API sans redistribuer dans Git."
docker run --rm --network bridge -v "$ROOT:/workspace" -w /workspace python:3.12-slim python scripts/cache-yoga-api-media.py
cp -p .env ".env.bak.$(date +%Y%m%d%H%M%S)"
if grep -q '^SICHOSANA_BIND=' .env; then
  sed -i 's/^SICHOSANA_BIND=.*/SICHOSANA_BIND=192.168.1.69/' .env
else printf '\nSICHOSANA_BIND=192.168.1.69\n' >> .env; fi
if grep -q '^SICHOSANA_ASTRO_ENABLED=' .env; then
  sed -i 's/^SICHOSANA_ASTRO_ENABLED=.*/SICHOSANA_ASTRO_ENABLED=1/' .env
else printf 'SICHOSANA_ASTRO_ENABLED=1\n' >> .env; fi
chmod 600 .env

echo "[SichoSana] Validation Compose sur réseau bridge historique."
docker compose -f compose.yaml -p sichosana config -q
docker compose -f compose.yaml -p sichosana up -d --build --no-deps
sleep 4

echo "[SichoSana] Contrôles publics sur IP NAS."
curl -fsS --max-time 10 http://192.168.1.69:18887/api/health
printf '\n'
curl -fsS --max-time 10 http://192.168.1.69:18887/api/v1/auth/config
printf '\n'
echo "[SichoSana] Pack voix :"
docker exec -i sichosana-app python - <<'PY'
import json
from pathlib import Path
p=Path('/app/static/voice/vivienne-fr-v2')
m=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
missing=[x['src'] for x in m['files'].values() if not (p/x['src']).is_file()]
if missing:
    raise SystemExit('Fichiers vocaux absents : '+str(missing[:6]))
print('PACK_AUDIO_OK',len(m['files']),'fichiers MP3')
PY
echo "[SichoSana] Mise à jour effectuée. Aucun autre conteneur ni tunnel modifié."
echo "[SichoSana] Adresse : https://yoga.sicho.cc.cd"
echo "[SichoSana] SMTP Gmail (optionnel): sh scripts/configure-smtp-gmail-qnap.sh"
