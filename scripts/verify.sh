#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

echo "=== AuditPilot Standard Verification ==="

# 1. Compile check
echo "[1/4] compileall backend/app"
"$BACKEND/.venv/bin/python" -m compileall "$BACKEND/app" -q

# 2. Tests
echo "[2/4] pytest"
"$BACKEND/.venv/bin/python" -m pytest "$BACKEND" -q

# 3. Lint
echo "[3/4] ruff check"
"$BACKEND/.venv/bin/ruff" check "$BACKEND"

# 4. Frontend build
echo "[4/4] frontend build"
cd "$FRONTEND" && npm run build -- --logLevel error

echo ""
echo "=== All checks passed ==="
