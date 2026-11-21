#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

source app/config.conf

PASS=0
FAIL=0

check() {
    local description="$1"
    shift

    if "$@" >/dev/null 2>&1; then
        printf '[PASS] %s\n' "$description"
        PASS=$((PASS + 1))
    else
        printf '[FAIL] %s\n' "$description"
        FAIL=$((FAIL + 1))
    fi
}

http_check() {
    local path="$1"
    local expected="$2"
    local actual

    actual=$(curl -sS --max-time 5 \
        -o /dev/null -w '%{http_code}' \
        "http://$APP_HOST:$APP_PORT/$path") || return 1

    [[ "$actual" == "$expected" ]]
}

content_check() {
    local content

    content=$(curl -fsS --max-time 5 \
        "http://$APP_HOST:$APP_PORT/") || return 1

    grep -q "Linux Operations Lab" <<< "$content"
}

socket_check() {
    local sockets

    sockets=$(ss -H -ltn "sport = :$APP_PORT") || return 1

    awk -v expected="$APP_HOST:$APP_PORT" '
        $4 == expected { found=1 }
        $4 != expected { invalid=1 }
        END { exit !(found && !invalid) }
    ' <<< "$sockets"
}

backup_check() {
    local archives

    shopt -s nullglob
    archives=(backups/operations_*.tar.gz.sha256)

    (( ${#archives[@]} > 0 )) || return 1

    sha256sum -c "${archives[-1]}"
}

echo "========================================"
echo " DECODELABS | ACCEPTANCE TEST SUITE"
echo "========================================"
echo "Timestamp: $(date -Iseconds)"
echo "Version: $APP_VERSION"
echo

echo "01 | FILESYSTEM VALIDATION"

check "Application directory exists" test -d app
check "Public directory exists" test -d app/public
check "Log directory exists" test -d app/logs
check "Backup directory exists" test -d backups
check "Evidence directory exists" test -d evidence
check "Scripts directory exists" test -d scripts
check "Application file populated" test -s app/index.html
check "Configuration populated" test -s app/config.conf
check "Operational logs populated" test -s app/logs/server.log
check "Original log backup exists" test -s app/logs/server.bak

check "Public application matches source" \
    cmp app/index.html app/public/index.html

check "Original HTML backup matches source" \
    cmp app/index.html backups/index.html.bak

echo
echo "02 | CONFIGURATION VALIDATION"

check "Application name configured" \
    test "$APP_NAME" = "Linux_Operations_Lab"

check "Application version configured" \
    test "$APP_VERSION" = "1.0.0"

check "Development environment configured" \
    test "$APP_ENV" = "development"

check "Localhost binding configured" \
    test "$APP_HOST" = "127.0.0.1"

check "Application port configured" \
    test "$APP_PORT" = "8095"

echo
echo "03 | APPLICATION AND NETWORK"

check "HTTP health check returns 200" http_check "" 200
check "Correct application content served" content_check
check "Missing resource returns 404" http_check "missing.html" 404
check "Configuration not exposed" http_check "config.conf" 404
check "Server logs not exposed" http_check "logs/server.log" 404
check "Backup files not exposed" http_check "index.html.bak" 404
check "Listening socket restricted to localhost" socket_check

echo
echo "04 | SCRIPT VALIDATION"

for script in scripts/*.sh; do
    check "Syntax: $script" bash -n "$script"
    check "Executable: $script" test -x "$script"
done

check "Operations CLI available" \
    bash scripts/ops.sh help

check "Security audit passes" \
    bash scripts/security-audit.sh

echo
echo "05 | BACKUP AND RECOVERY"

check "Latest backup integrity verified" backup_check

check "Isolated recovery succeeds" \
    bash scripts/recovery-test.sh

echo
echo "========================================"
echo " FINAL ACCEPTANCE REPORT"
echo "========================================"

echo "Total tests : $((PASS + FAIL))"
echo "Passed      : $PASS"
echo "Failed      : $FAIL"

if (( FAIL == 0 )); then
    echo "Pass rate   : 100%"
    echo "Status      : ALL TESTS PASSED"
    echo "Release     : ACCEPTED"
else
    echo "Status      : REVIEW REQUIRED"
    echo "Release     : NOT ACCEPTED"
    exit 1
fi

echo "========================================"
