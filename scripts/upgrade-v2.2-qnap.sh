#!/bin/sh
# QNAP avec ou sans Git : choisir automatiquement la méthode disponible.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if command -v git >/dev/null 2>&1; then
  exec sh "$ROOT/upgrade-v2.1-qnap.sh"
else
  exec sh "$ROOT/upgrade-v2.2-no-git-qnap.sh"
fi
