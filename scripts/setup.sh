#!/usr/bin/env bash
set -euo pipefail
umask 077

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "Initializing Linux Operations Lab..."

for cmd in python3 curl ss tar sha256sum git; do
    command -v "$cmd" >/dev/null || {
        echo "Missing dependency: $cmd"
        exit 1
    }
done

mkdir -p app/logs app/src app/public
mkdir -p backups evidence docs

cp app/index.html app/public/index.html
cp app/index.html backups/index.html.bak

if [[ ! -f app/config.conf ]]; then
    cp app/config.example.conf app/config.conf
fi

if [[ ! -s app/logs/server.log ]]; then
    echo "Application initialized" > app/logs/server.log
fi

if [[ ! -s app/logs/server.bak ]]; then
    echo "Started" > app/logs/server.bak
fi

chmod 600 app/config.conf
chmod 644 app/index.html
chmod 644 app/public/index.html
chmod 755 app/public

chmod 750 app/logs scripts
chmod 640 app/logs/server.log app/logs/server.bak
chmod 750 scripts/*.sh

chmod 700 backups evidence
chmod 600 backups/index.html.bak

echo "SETUP STATUS: SUCCESS"
echo "Start: ./scripts/ops.sh start"
