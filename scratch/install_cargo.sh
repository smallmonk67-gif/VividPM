#!/bin/bash
echo '--- VividPM Backend Installer ---'
echo 'Target: Cargo (Rust)'
echo 'Command: sudo pacman -S --noconfirm rust'
echo '---------------------------------'

sudo pacman -S --noconfirm rust

if [ $? -eq 0 ]; then
    echo
    echo 'SUCCESS: Cargo (Rust) installed successfully.'
    sleep 2
else
    echo
    echo 'ERROR: Installation failed with exit code $?'
    echo 'Press Enter to close this window...'
    read
fi
