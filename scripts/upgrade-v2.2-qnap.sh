#!/bin/sh
# Compatibilité : même upgrade QNAP non destructif, complété par assets Yoga API.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec sh "$ROOT/upgrade-v2.1-qnap.sh"
