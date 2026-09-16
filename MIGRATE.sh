#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
case "${1:---check}" in
  --check)
    test -f BLUEPRINT.md && test -f .env && test -f compose.yaml
    command -v docker >/dev/null
    docker compose version >/dev/null
    test -d backups
    echo 'MIGRATE check: OK'
    ;;
  --install) make up; make migrate; make doctor ;;
  --migrate) make migrate ;;
  --verify) make doctor ;;
  --restore)
    test -n "${2:-}" || { echo 'Usage: ./MIGRATE.sh --restore backups/<timestamp>' >&2; exit 2; }
    make restore BACKUP="$2"
    ;;
  --rollback)
    echo "ERROR: rollback non opérationnel en LOT 0; aucune release production n'est configurée." >&2
    exit 2
    ;;
  *)
    echo 'Usage: ./MIGRATE.sh [--check|--install|--migrate|--verify|--restore <backup>|--rollback]' >&2
    exit 2
    ;;
esac
