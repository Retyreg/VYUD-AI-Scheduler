#!/usr/bin/env bash
# deploy.sh — deploy VYUD Publisher (v2.1 FastAPI + SvelteKit) to the server.
#
# Usage (run on the server from the repo root):
#   bash scripts/deploy.sh                   # backend only (default)
#   bash scripts/deploy.sh --with-frontend   # backend + frontend rebuild
#   bash scripts/deploy.sh --setup-venv      # recreate backend venv first
#
# Example via SSH:
#   ssh root@SERVER "cd /root/publisher_app && bash scripts/deploy.sh"

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$REPO_DIR/backend"
FRONTEND_DIR="$REPO_DIR/frontend~"
VENV_DIR="$BACKEND_DIR/venv"
BACKEND_SERVICE="${BACKEND_SERVICE:-publisher-api}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-publisher-frontend}"

WITH_FRONTEND=false
SETUP_VENV=false
for arg in "$@"; do
    case "$arg" in
        --with-frontend) WITH_FRONTEND=true ;;
        --setup-venv)    SETUP_VENV=true ;;
    esac
done

echo "=== VYUD Publisher deploy ==="
echo "Repo     : $REPO_DIR"
echo "Backend  : $BACKEND_SERVICE"
echo "Frontend : $FRONTEND_SERVICE (rebuild=$WITH_FRONTEND)"
echo ""

cd "$REPO_DIR"

# 1. Pull latest code (merge strategy — never rebase on server)
echo "[1/5] Pulling latest code..."
git fetch origin main
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "      WARNING: Uncommitted changes detected — merging anyway."
fi
git pull --no-rebase origin main
echo "      Done. Current commit: $(git rev-parse --short HEAD)"

# 2. Set up or update backend venv
if [[ "$SETUP_VENV" == "true" ]] || [[ ! -x "$VENV_DIR/bin/uvicorn" ]]; then
    echo "[2/5] Setting up backend venv (uvicorn missing or --setup-venv requested)..."
    bash "$REPO_DIR/scripts/setup_venv.sh"
else
    echo "[2/5] Updating backend dependencies..."
    "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt" --quiet
fi
echo "      Done."

# 3. Restart backend
echo "[3/5] Restarting backend service ($BACKEND_SERVICE)..."
if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    systemctl restart "$BACKEND_SERVICE"
else
    systemctl start "$BACKEND_SERVICE"
fi
sleep 2
# Quick health check
if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "      Backend healthy ✓"
else
    echo "      WARNING: /health not responding — check logs:"
    echo "        journalctl -u $BACKEND_SERVICE -n 30"
fi

# 4. (Optional) Rebuild frontend
if [[ "$WITH_FRONTEND" == "true" ]]; then
    echo "[4/5] Building frontend..."
    if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
        echo "      ERROR: $FRONTEND_DIR/package.json not found!" >&2
        echo "      Run: cd $FRONTEND_DIR && npm install" >&2
        exit 1
    fi
    cd "$FRONTEND_DIR"
    npm install --silent
    npm run build
    systemctl restart "$FRONTEND_SERVICE"
    echo "      Frontend rebuilt and restarted ✓"
    cd "$REPO_DIR"
else
    echo "[4/5] Skipping frontend rebuild (pass --with-frontend to rebuild)."
fi

# 5. Final status
echo "[5/5] Status:"
systemctl status "$BACKEND_SERVICE" --no-pager -l | head -8
echo ""
echo "=== Deploy complete ==="
echo "Logs  : journalctl -u $BACKEND_SERVICE -n 50"
echo "Health: curl -s http://localhost:8000/health"
