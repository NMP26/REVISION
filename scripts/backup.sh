#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .env
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
out_dir="$ROOT_DIR/backups/$timestamp"
mkdir -p "$out_dir"
chmod 700 "$out_dir"
docker compose -p revision-prix --env-file .env -f compose.yaml exec -T revision-prix-postgres pg_dump --format=custom --no-owner --no-privileges -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$out_dir/postgresql.dump"
test -s "$out_dir/postgresql.dump"
docker compose -p revision-prix --env-file .env -f compose.yaml exec -T revision-prix-backend python manage.py showmigrations --plan > "$out_dir/migrations.txt"
{
  echo "timestamp_utc=$timestamp"
  echo "application_version=$(tr -d '[:space:]' < VERSION)"
  echo "compose_project=revision-prix"
  echo "database_schema=LOT0"
  echo "postgres_image=postgres:16.9-alpine3.21"
} > "$out_dir/metadata.txt"
sha256sum "$out_dir/postgresql.dump" "$out_dir/migrations.txt" "$out_dir/metadata.txt" > "$out_dir/SHA256SUMS"
chmod 600 "$out_dir"/*
echo "Backup created: $out_dir"
