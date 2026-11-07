#!/bin/sh
# SichoSana QNAP V2.3 — avec ou sans Git natif.
# Le mode sans Git est la référence pour le QNAP NAS-DAMIEN.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if command -v git >/dev/null 2>&1; then
  exec sh "$ROOT/upgrade-v2.1-qnap.sh"
fi
exec sh "$ROOT/upgrade-v2.3-no-git-qnap.sh"
