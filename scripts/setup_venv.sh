#!/usr/bin/env bash
# setup_venv.sh — Create (or recreate) the Python virtual environment for
# the VYUD Publisher backend (v2.1 FastAPI).
#
# Run from the repository root on the VPS:
#   bash scripts/setup_venv.sh
#
# After this script completes, restart the service:
#   systemctl restart publisher-api

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$REPO_DIR/backend"
VENV_DIR="$BACKEND_DIR/venv"

echo "=== VYUD Publisher — backend venv setup ==="
echo "Backend dir : $BACKEND_DIR"
echo "Venv dir    : $VENV_DIR"
echo ""

# Ensure Python 3 is available
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install it first:" >&2
    echo "  apt install python3 python3-venv python3-pip" >&2
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "Python: $PYTHON_VERSION"

# Remove stale venv if asked
if [[ "${1:-}" == "--clean" ]]; then
    echo "Removing existing venv..."
    rm -rf "$VENV_DIR"
fi

# Create venv
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "Venv created."
else
    echo "Venv already exists (use --clean to recreate)."
fi

# Install / upgrade dependencies
echo "Installing dependencies from backend/requirements.txt..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
echo "Dependencies installed."

# Copy .env if it doesn't exist
if [[ ! -f "$BACKEND_DIR/.env" ]]; then
    if [[ -f "$BACKEND_DIR/.env.example" ]]; then
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        echo ""
        echo "WARNING: Created .env from .env.example — fill in your real API keys!"
        echo "  nano $BACKEND_DIR/.env"
    fi
fi

echo ""
echo "=== Setup complete ==="
echo "Verify uvicorn is available:"
"$VENV_DIR/bin/uvicorn" --version
echo ""
echo "Next steps:"
echo "  1. Ensure $BACKEND_DIR/.env has all required keys"
echo "  2. systemctl restart publisher-api"
echo "  3. curl -s http://localhost:8000/health"
