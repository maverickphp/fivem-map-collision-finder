# Builds "FiveM Map Collision Finder" into a single standalone Windows .exe.
# The resulting .exe bundles Python itself, so it runs on any Windows PC with
# nothing else installed. Run this from a machine that HAS Python:
#
#   powershell -ExecutionPolicy Bypass -File build.ps1
#
$ErrorActionPreference = "Stop"

Write-Host "Installing/upgrading PyInstaller..." -ForegroundColor Cyan
python -m pip install --upgrade pyinstaller

Write-Host "Building the executable..." -ForegroundColor Cyan
python -m PyInstaller --noconfirm --onefile --windowed `
    --name "FiveM Map Collision Finder" app.py

Write-Host ""
Write-Host "Done. Your app is here:" -ForegroundColor Green
Write-Host "  dist\FiveM Map Collision Finder.exe"
Write-Host "Copy that single file to any Windows PC and double-click it."
