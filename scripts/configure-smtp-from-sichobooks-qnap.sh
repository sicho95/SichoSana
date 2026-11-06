#!/bin/sh
# SichoSana : reprise locale du SMTP Gmail SichoBooks, sans partage de secrets.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
echo "[SichoSana] Recherche d'une configuration SMTP Gmail SichoBooks existante..."
SOURCE="$(docker ps --format '{{.Names}}' | grep -Ei 'sichobook|books' | head -n 1 || true)"
if [ -z "$SOURCE" ]; then
  echo "Aucun conteneur SichoBooks trouvé ; utiliser : sh scripts/configure-smtp-gmail-qnap.sh"
  exit 1
fi
echo "Conteneur source détecté : $SOURCE (aucun mot de passe ne sera affiché)."
# Il n'est pas demandé de saisir le secret de SichoBooks à nouveau.
docker inspect "$SOURCE" | docker run --rm --network bridge -i   -v "$ROOT:/workspace" -w /workspace python:3.12-slim   python scripts/adopt-sichobooks-smtp.py

docker compose -f compose.yaml -p sichosana config -q
docker compose -f compose.yaml -p sichosana up -d --no-deps --force-recreate
echo "[SichoSana] Configuration appliquée sur le conteneur SichoSana uniquement."
echo "Un email de recette doit encore être envoyé et vérifié avant de déclarer le SMTP opérationnel."
