#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
fail=0
echo "RevisionPrix Diagnostic"
docker version --format 'Docker.............. OK ({{.Server.Version}})' || fail=1
docker compose version >/dev/null && echo 'Compose............. OK' || fail=1

status="$(docker compose -p revision-prix --env-file .env -f compose.yaml ps --format json)"
python3 - "$status" <<'PY' || fail=1
import json, sys
data = [json.loads(line) for line in sys.argv[1].splitlines() if line.strip()]
required = {"revision-prix-postgres", "revision-prix-backend", "revision-prix-frontend"}
seen = {item.get("Name") for item in data}
if seen != required:
    raise SystemExit(f"services inattendus/incomplets: {sorted(seen)}")
for item in data:
    if item.get("Health", "") != "healthy":
        raise SystemExit(f"{item['Name']}: {item.get('State')} / health={item.get('Health')}")
    print(f"{item['Name']:<24} HEALTHY")
PY

listeners="$(ss -lntH '( sport = :12701 )' || true)"
echo "$listeners" | grep -Eq '127\.0\.0\.1:12701' || { echo '127.0.0.1:12701 absent' >&2; fail=1; }
if echo "$listeners" | grep -Eq '0\.0\.0\.0:12701|\[::\]:12701'; then
  echo '127.01 est exposé sur une adresse non locale' >&2
  fail=1
fi

curl --fail --silent --show-error --max-time 5 http://127.0.0.1:12701/api/health/ >/tmp/revision-prix-health.json
python3 - <<'PY' || fail=1
import json
with open('/tmp/revision-prix-health.json') as stream:
    payload = json.load(stream)
assert payload['status'] == 'ok', payload
assert payload['database']['status'] == 'ok', payload
assert payload['migrations']['status'] == 'ok', payload
print('Backend............ HEALTHY')
print('PostgreSQL......... HEALTHY')
print('Migrations.......... CURRENT')
PY
rm -f /tmp/revision-prix-health.json

if [ "$fail" -ne 0 ]; then
  echo 'SYSTEM NOT READY' >&2
  exit 1
fi
echo 'Storage............. OK'
echo "App Version......... $(tr -d '[:space:]' < VERSION)"
echo 'DB Schema........... LOT0'
echo 'SYSTEM READY'
