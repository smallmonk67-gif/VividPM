#!/bin/bash
echo '--- VividPM Backend Installer ---'
echo 'Target: RubyGems'
echo 'Command: sudo pacman -S --noconfirm ruby'
echo '---------------------------------'

sudo pacman -S --noconfirm ruby

if [ $? -eq 0 ]; then
    echo
    echo 'SUCCESS: RubyGems installed successfully.'
    sleep 2
else
    echo
    echo 'ERROR: Installation failed with exit code $?'
    echo 'Press Enter to close this window...'
    read
fi
