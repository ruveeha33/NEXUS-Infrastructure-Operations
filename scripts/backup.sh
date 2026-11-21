#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STAMP=$(date +%Y%m%d_%H%M%S_%N)
ARCHIVE="backups/operations_${STAMP}.tar.gz"

mkdir -p backups

echo "Creating compressed application backup..."

tar -czf "$ARCHIVE" \
    app/index.html \
    app/config.conf \
    app/public \
    scripts

chmod 600 "$ARCHIVE"

sha256sum "$ARCHIVE" > "${ARCHIVE}.sha256"

echo
echo "Verifying backup integrity..."

sha256sum -c "${ARCHIVE}.sha256"

echo
echo "Archive contents:"
tar -tzf "$ARCHIVE"

echo
echo "Backup size: $(du -h "$ARCHIVE" | cut -f1)"
echo "Backup location: $ARCHIVE"
echo "Timestamp: $(date -Iseconds)"
echo "BACKUP STATUS: SUCCESS"
