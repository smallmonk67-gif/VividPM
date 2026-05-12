#!/bin/bash
echo '--- VividPM Backend Installer ---'
echo 'Target: npm (Node.js)'
echo 'Command: sudo pacman -S --noconfirm npm'
echo '---------------------------------'

sudo pacman -S --noconfirm npm

if [ $? -eq 0 ]; then
    echo
    echo 'SUCCESS: npm (Node.js) installed successfully.'
    sleep 2
else
    echo
    echo 'ERROR: Installation failed with exit code $?'
    echo 'Press Enter to close this window...'
    read
fi
