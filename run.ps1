# run.ps1 — Portable PowerShell script to launch Vivid Package Manager on Windows

# Get the directory of the script
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

Write-Host "Starting Vivid Package Manager..." -ForegroundColor Cyan

# Check for local virtual environment
$VENV_BIN = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (Test-Path $VENV_BIN) {
    Write-Host "Using virtual environment: $VENV_BIN" -ForegroundColor Gray
    & $VENV_BIN launcher.py
} else {
    Write-Host "Using system python" -ForegroundColor Gray
    python launcher.py
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nError: Application failed to start." -ForegroundColor Red
    Write-Host "Make sure you have installed the requirements:" -ForegroundColor Gray
    Write-Host "pip install customtkinter Pillow"
    Pause
}
