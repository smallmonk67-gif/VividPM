#!/bin/bash
# run.sh — Portable shell script to launch the Vivid Package Manager

# Get the absolute path to the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Priority: Use the local virtual environment if it exists
if [ -f ".venv/bin/python" ]; then
    ./.venv/bin/python launcher.py "$@" > /dev/null 2>&1 & disown
else
    # Fallback to system python
    python3 launcher.py "$@" > /dev/null 2>&1 & disown
fi

clear
echo "[Launcher] Vivid Package Manager is starting in the background..."
echo "[Launcher] You can safely close this terminal."
sleep 1
exit 0
