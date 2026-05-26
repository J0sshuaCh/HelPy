#!/usr/bin/env bash
# Run the application using the project's .venv (Unix/macOS)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [ -d "$VENV_DIR" ]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
else
  echo ".venv not found. Running install.sh to create it..."
  "$ROOT_DIR/scripts/install.sh"
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
fi

python -m app.main
