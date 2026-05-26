#!/usr/bin/env bash
# Create a virtualenv in .venv and install requirements (Unix/macOS)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

echo "Using project root: $ROOT_DIR"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Python not found in PATH. Install Python 3.8+ and retry." >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtualenv in $VENV_DIR"
  "$PY" -m venv "$VENV_DIR"
fi

echo "Installing pip requirements"
"$VENV_DIR/bin/pip" install --upgrade pip
if [ -f "$ROOT_DIR/requirements.txt" ]; then
  "$VENV_DIR/bin/pip" install -r "$ROOT_DIR/requirements.txt"
else
  echo "requirements.txt not found in project root." >&2
  exit 1
fi

echo "Installation complete. To run the app:"
echo "  source $VENV_DIR/bin/activate"
echo "  python -m app.main"
