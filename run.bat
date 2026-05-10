@echo off
REM run.bat — Double-clickable launcher for Vivid Package Manager on Windows

set DIR=%~dp0
cd /d %DIR%

echo Starting Vivid Package Manager...

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" launcher.py
) else if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" launcher.py
) else (
    start "" pythonw launcher.py || python launcher.py
)

exit /b 0

if %ERRORLEVEL% neq 0 (
    echo.
    echo Error: Application failed to start.
    echo Make sure you have installed the requirements:
    echo pip install customtkinter Pillow
    pause
)
