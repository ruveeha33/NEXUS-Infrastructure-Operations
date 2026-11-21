#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PASS=0
FAIL=0

check_mode() {
    local target="$1"
    local expected="$2"
    local actual

    actual=$(stat -c '%a' "$target")

    if [[ "$actual" == "$expected" ]]; then
        echo "[PASS] $target | Mode: $actual"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $target | Expected: $expected | Actual: $actual"
        FAIL=$((FAIL + 1))
    fi
}

echo "========================================"
echo " LINUX OPERATIONS | SECURITY AUDIT"
echo "========================================"

echo "Timestamp: $(date -Iseconds)"
echo "User: $(whoami)"
echo

check_mode app/config.conf 600
check_mode app/index.html 644
check_mode app/public/index.html 644
check_mode app/public 755
check_mode app/logs 750
check_mode app/logs/server.log 640
check_mode app/logs/server.bak 640
check_mode backups 700
check_mode backups/index.html.bak 600
check_mode evidence 700
check_mode scripts/start.sh 750
check_mode scripts/monitor.sh 750
check_mode scripts/live-logs.sh 750
check_mode scripts/security-audit.sh 750

echo
echo "WORLD-WRITABLE FILES"
echo "----------------------------------------"

EXPOSED=$(find app scripts backups evidence \
    -type f -perm -0002 -print)

if [[ -z "$EXPOSED" ]]; then
    echo "[PASS] No world-writable files detected"
    PASS=$((PASS + 1))
else
    printf '%s\n' "$EXPOSED"
    FAIL=$((FAIL + 1))
fi

echo
echo "AUDIT SUMMARY"
echo "----------------------------------------"
echo "Passed: $PASS"
echo "Failed: $FAIL"

if [[ "$FAIL" -eq 0 ]]; then
    echo "Security status: PASS"
else
    echo "Security status: REVIEW REQUIRED"
    exit 1
fi

echo "========================================"
