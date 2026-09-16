#!/usr/bin/env bash
set -Eeuo pipefail
echo "ERROR: rollback désactivé en LOT 0; aucune release de production n'est configurée." >&2
exit 2
