#!/bin/sh
# SichoSana — vérifications non destructives. Ne jamais modifier cloudflared ni Tailscale ici.
set -eu
MODE="${1:---check}"
case "$MODE" in --check|--apply) ;; *) echo "Usage: sh scripts/deploy-qnap.sh --check|--apply" >&2; exit 2;; esac
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
echo "[SichoSana] Projet : $ROOT"
command -v docker >/dev/null || { echo "[ERREUR] Docker absent."; exit 1; }
docker compose version || { echo "[ERREUR] Docker Compose v2 absent."; exit 1; }
docker compose -f compose.yaml config >/dev/null || { echo "[ERREUR] Compose invalide."; exit 1; }
PORT="${SICHOSANA_PORT:-18887}"
echo "[SichoSana] Port envisagé : $PORT (bind ${SICHOSANA_BIND:-127.0.0.1})"
if [ "$MODE" = "--check" ]; then
  if command -v ss >/dev/null 2>&1; then
    ss -lnt | grep -E "[:.]$PORT[[:space:]]" && echo "[ATTENTION] Le port apparaît occupé. Contrôler avant --apply." || true
  fi
  echo "[SichoSana] PRÉCONTRÔLE OK. Aucun conteneur, tunnel, DNS ni route modifié."
  exit 0
fi
if [ -e runtime ] && [ ! -d runtime ]; then echo "[ERREUR] runtime n'est pas un dossier."; exit 1; fi
mkdir -p runtime
chmod 700 runtime
docker compose -f compose.yaml -p sichosana up -d --build --no-deps
echo "[SichoSana] Application locale lancée. Contrôler http://127.0.0.1:$PORT/api/health"
echo "[SichoSana] Routes Cloudflare et Tailscale volontairement inchangées : phase séparée."
