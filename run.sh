#!/bin/bash
# run.sh — Portable shell script to launch the Package Manager

# Get the absolute path to the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Priority: Use the local virtual environment if it exists
if [ -f ".venv/bin/python" ]; then
    echo "[Launcher] Using local virtual environment..."
    ./.venv/bin/python launcher.py "$@"
else
    # Fallback to system python
    echo "[Launcher] Local venv not found, trying system python..."
    python3 launcher.py "$@"
fi
