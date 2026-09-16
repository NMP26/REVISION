#!/usr/bin/env bash
set -Eeuo pipefail
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 backups/<timestamp>" >&2
  exit 2
fi
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$ROOT_DIR/$1"
if [ ! -f "$BACKUP_DIR/postgresql.dump" ]; then
  echo "ERROR: backup PostgreSQL absent: $BACKUP_DIR/postgresql.dump" >&2
  exit 1
fi
echo "ERROR: restauration bloquée par défaut en LOT 0; autorisation et procédure d'arrêt requises." >&2
exit 2
