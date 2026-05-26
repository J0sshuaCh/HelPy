# Windows PowerShell install script: creates .venv and installs requirements
param()
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root '.venv'

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error 'Python not found in PATH. Install Python 3.8+ and retry.'
    exit 1
}

if (-not (Test-Path -LiteralPath $Venv)) {
    python -m venv $Venv
}

if (Test-Path -LiteralPath (Join-Path $Root 'requirements.txt')) {
    & "$Venv\Scripts\pip.exe" install -r (Join-Path $Root 'requirements.txt')
} else {
    Write-Error 'requirements.txt not found in project root.'
    exit 1
}

Write-Host "Installation complete. To run the app (PowerShell):"
Write-Host "  & $Venv\Scripts\Activate.ps1"
Write-Host "  python -m app.main"
