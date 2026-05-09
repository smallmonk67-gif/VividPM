@echo off
REM run.bat — Double-clickable launcher for Vivid Package Manager on Windows

set DIR=%~dp0
cd /d %DIR%

echo Starting Vivid Package Manager...

if exist ".venv\Scripts\python.exe" (
    echo Using virtual environment...
    ".venv\Scripts\python.exe" launcher.py
) else (
    echo Using system python...
    python launcher.py
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo Error: Application failed to start.
    echo Make sure you have installed the requirements:
    echo pip install customtkinter Pillow
    pause
)
