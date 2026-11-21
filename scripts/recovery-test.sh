#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

shopt -s nullglob
ARCHIVES=(backups/operations_*.tar.gz)

if (( ${#ARCHIVES[@]} == 0 )); then
    echo "ERROR: No backup archives found."
    exit 1
fi

ARCHIVE="${ARCHIVES[-1]}"

echo "========================================"
echo " DISASTER RECOVERY TEST"
echo "========================================"

echo "Selected archive: $ARCHIVE"

echo
echo "[1] Verifying archive integrity"
sha256sum -c "${ARCHIVE}.sha256"

echo
echo "[2] Creating isolated recovery directory"

RECOVERY=$(mktemp -d "$ROOT/backups/recovery.XXXXXX")

echo "Recovery directory: $RECOVERY"

echo
echo "[3] Extracting backup"

tar -xzf "$ARCHIVE" -C "$RECOVERY"

echo
echo "[4] Comparing restored files"

cmp app/index.html "$RECOVERY/app/index.html"
echo "PASS: Application file matches"

cmp app/config.conf "$RECOVERY/app/config.conf"
echo "PASS: Configuration file matches"

diff -r app/public "$RECOVERY/app/public"
echo "PASS: Public application matches"

diff -r scripts "$RECOVERY/scripts"
echo "PASS: Operational scripts match"

echo
echo "[5] Verifying restored startup script"

bash -n "$RECOVERY/scripts/start.sh"

echo "PASS: Restored startup script is valid"

echo
echo "RECOVERY STATUS: SUCCESS"
echo "Original application remains unchanged."
echo "Recovered files: $RECOVERY"
