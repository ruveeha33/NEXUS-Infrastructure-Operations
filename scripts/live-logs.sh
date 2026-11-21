#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "LIVE SERVER LOGS"
echo "Press Ctrl+C to exit monitoring."
echo "----------------------------------------"

exec tail -f app/logs/server.log
