#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

source app/config.conf

LOG="app/logs/server.log"

STATUS=$(curl -s --max-time 5 \
    -o /dev/null -w '%{http_code}' \
    "http://$APP_HOST:$APP_PORT/" || true)

TOTAL=$(grep -Ec '" [1-5][0-9]{2} ' "$LOG" || true)
SUCCESS=$(grep -c '" 200 ' "$LOG" || true)
CACHED=$(grep -c '" 304 ' "$LOG" || true)
NOT_FOUND=$(grep -c '" 404 ' "$LOG" || true)
ERRORS=$(grep -Ec '" [45][0-9]{2} ' "$LOG" || true)

echo "========================================"
echo " LINUX OPERATIONS | MONITORING REPORT"
echo "========================================"
echo "Timestamp       : $(date -Iseconds)"
echo "Application     : $APP_NAME"
echo "Environment     : $APP_ENV"
echo "HTTP status     : $STATUS"
echo "Total requests  : $TOTAL"
echo "HTTP 200        : $SUCCESS"
echo "HTTP 304        : $CACHED"
echo "HTTP 404        : $NOT_FOUND"
echo "HTTP errors     : $ERRORS"
echo "Log size        : $(du -h "$LOG" | cut -f1)"

if [[ "$STATUS" == "200" ]]; then
    echo "Service status  : HEALTHY"
else
    echo "Service status  : UNAVAILABLE"
fi

echo
echo "LATEST LOG ENTRIES"
echo "----------------------------------------"
tail -n 5 "$LOG"

echo "========================================"
