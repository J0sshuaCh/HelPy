param(
    [switch]$Clean = $false,
    [switch]$NoUPX = $false
)

$ErrorActionPreference = "Stop"

# Corregido: Calculamos la raíz del proyecto un nivel arriba de 'scripts/'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvScripts = Join-Path $VenvDir "Scripts"
$VenvPython = Join-Path $VenvScripts "python.exe"

$SpecFile = Join-Path $ProjectRoot "helpy.spec"
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HelPy - PyInstaller Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $VenvPython)) {
    Write-Host "ERROR: Virtual env python not found at $VenvPython" -ForegroundColor Red
    Write-Host "Verifica si el entorno virtual existe en $VenvDir" -ForegroundColor Yellow
    exit 1
}

Write-Host "Python: $VenvPython" -ForegroundColor Gray

# Verificar PyInstaller
$pyinst = & $VenvPython -c "import PyInstaller; print(PyInstaller.__version__)" 2>$null
if (-not $pyinst) {
    Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
    & $VenvPython -m pip install pyinstaller
    $pyinst = & $VenvPython -c "import PyInstaller; print(PyInstaller.__version__)" 2>$null
}
Write-Host "PyInstaller: $pyinst" -ForegroundColor Gray

# Limpiar si se solicita
if ($Clean) {
    if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir; Write-Host "Cleaned dist/" -ForegroundColor Yellow }
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir; Write-Host "Cleaned build/" -ForegroundColor Yellow }
}

Write-Host ""
Write-Host "Building HelPy..." -ForegroundColor Green

$args = @($SpecFile, "--clean", "-y")
if ($NoUPX) { $args += "--noupx" }

& $VenvPython -m PyInstaller @args

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build FAILED!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Build completed!" -ForegroundColor Green
$outputDir = Join-Path $DistDir "HelPy"
Write-Host "Output: $outputDir" -ForegroundColor Cyan

$exePath = Join-Path $outputDir "HelPy.exe"
if (Test-Path $exePath) {
    $size = (Get-Item $exePath).Length / 1MB
    $totalSize = (Get-ChildItem -Recurse $outputDir | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "HelPy.exe: $([math]::Round($size, 1)) MB" -ForegroundColor Gray
    Write-Host "Total: $([math]::Round($totalSize, 1)) MB" -ForegroundColor Gray
}

Write-Host ""
# Limpiar el inference_server.exe duplicado del root de dist/
$rootServerExe = Join-Path $DistDir "inference_server.exe"
if (Test-Path $rootServerExe) {
    Remove-Item -Force $rootServerExe
    Write-Host "Cleaned root inference_server.exe (duplicate)" -ForegroundColor Yellow
}

Write-Host "Done!" -ForegroundColor Cyan
