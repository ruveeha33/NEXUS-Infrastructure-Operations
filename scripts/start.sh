#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

source app/config.conf

echo "Starting $APP_NAME v$APP_VERSION"
echo "Environment: $APP_ENV"
echo "Address: http://$APP_HOST:$APP_PORT"

printf '[%s] [%s] Application starting on %s:%s\n' \
    "$(date -Iseconds)" "$LOG_LEVEL" \
    "$APP_HOST" "$APP_PORT" >> app/logs/server.log

exec python3 -u -m http.server "$APP_PORT" \
    --bind "$APP_HOST" \
    --directory app/public \
    >> app/logs/server.log 2>&1
