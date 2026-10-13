#!/usr/bin/env bash
# One-shot launcher for Whisper Doped.
#   ./run.sh            -> start in the menu bar
#   ./run.sh selftest   -> verify the environment
#   ./run.sh --console  -> terminal mode
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# Prefer Homebrew Python 3.12 on Apple Silicon.
PYTHON="${PYTHON:-$(command -v python3.12 || command -v python3)}"

if [[ ! -d .venv ]]; then
  echo "Creating virtual environment with $PYTHON ..."
  "$PYTHON" -m venv .venv
  ./.venv/bin/python -m pip install --upgrade pip wheel
  ./.venv/bin/python -m pip install -r requirements.txt
fi

exec ./.venv/bin/python -m whisper_doped "$@"
