# Windows PowerShell run script: activates .venv and runs the app
param()
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root '.venv'

if (-not (Test-Path -LiteralPath $Venv)) {
    Write-Host '.venv not found. Running install.ps1 to create it...'
    & "$PSScriptRoot\install.ps1"
}

& "$Venv\Scripts\Activate.ps1"
python -m app.main
