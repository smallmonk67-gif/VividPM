# run.ps1 — Portable PowerShell script to launch Vivid Package Manager on Windows

# Get the directory of the script
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

Write-Host "Starting Vivid Package Manager..." -ForegroundColor Cyan

# Check for local virtual environment
$VENV_BIN_W = Join-Path $PSScriptRoot ".venv\Scripts\pythonw.exe"
$VENV_BIN = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (Test-Path $VENV_BIN_W) {
    Start-Process $VENV_BIN_W -ArgumentList "launcher.py" -WindowStyle Hidden
} elseif (Test-Path $VENV_BIN) {
    Start-Process $VENV_BIN -ArgumentList "launcher.py" -WindowStyle Hidden
} else {
    try {
        Start-Process "pythonw" -ArgumentList "launcher.py" -WindowStyle Hidden -ErrorAction Stop
    } catch {
        Start-Process "python" -ArgumentList "launcher.py" -WindowStyle Hidden
    }
}

exit 0

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nError: Application failed to start." -ForegroundColor Red
    Write-Host "Make sure you have installed the requirements:" -ForegroundColor Gray
    Write-Host "pip install customtkinter Pillow"
    Pause
}
