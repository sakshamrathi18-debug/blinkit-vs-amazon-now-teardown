#!/bin/zsh
exec "$(dirname "$0")/.venv/bin/python" "$(dirname "$0")/tool/qc_audit.py" "$@"
