#!/usr/bin/env bash
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
MODE="--check"
if [ "$#" -gt 0 ]; then MODE="$1"; fi
case "$MODE" in
  --check|--apply) ;;
  *) echo "Usage : bash scripts/deploy-nas.sh --check | --apply"; exit 2 ;;
esac
printf '%s\n' "[SichoSana] Précontrôle non destructif"
command -v docker >/dev/null || { echo "Docker absent"; exit 2; }
docker compose version
docker compose -f docker-compose.yml config --quiet
if command -v ss >/dev/null && ss -ltn | grep -Eq '[:.]18765[[:space:]]'; then
  if ! docker ps --format '{{.Names}}' | grep -qx 'sichosana'; then
    echo '[SichoSana] Port 18765 occupé par un autre service : arrêt pour sécurité.'
    exit 3
  fi
fi
if [ "$MODE" = "--check" ]; then
  echo '[SichoSana] Vérification terminée. Aucun conteneur, tunnel ni DNS modifié.'
  exit 0
fi
docker compose up -d --build --no-deps sichosana
echo '[SichoSana] Seul le conteneur sichosana a été déployé.'
echo '[SichoSana] Point local : http://127.0.0.1:18765/api/v1/health'
echo '[SichoSana] Cloudflare Tunnel, DNS et Tailscale INCHANGÉS ; routes à ajouter séparément sur le tunnel existant.'
