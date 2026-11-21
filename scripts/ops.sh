#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

case "${1:-help}" in

    start)
        exec bash scripts/start.sh
        ;;

    status|monitor)
        exec bash scripts/monitor.sh
        ;;

    logs)
        exec bash scripts/live-logs.sh
        ;;

    audit)
        exec bash scripts/security-audit.sh
        ;;

    backup)
        exec bash scripts/backup.sh
        ;;

    recover)
        exec bash scripts/recovery-test.sh
        ;;

    verify)
        exec bash scripts/verify.sh
        ;;

    help)
        cat <<'HELP'
========================================
 DECODELABS | LINUX OPERATIONS CLI
========================================

Usage: ./scripts/ops.sh <command>

COMMAND       DESCRIPTION
----------------------------------------
start         Start application
status        Check operational health
monitor       Display monitoring report
logs          Watch live server logs
audit         Run security audit
backup        Create verified backup
recover       Test isolated recovery
verify        Run complete acceptance tests
help          Display available commands

========================================
HELP
        ;;

    *)
        echo "Unknown command: $1"
        echo "Run ./scripts/ops.sh help"
        exit 1
        ;;
esac
