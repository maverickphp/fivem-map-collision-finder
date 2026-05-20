@echo off
REM Builds "FiveM Map Collision Finder" into a single standalone Windows .exe.
REM The resulting .exe bundles Python itself, so it runs on any Windows PC with
REM nothing else installed. Just double-click this file on a PC that has Python.

echo Installing/upgrading PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto error

echo Building the executable...
python -m PyInstaller --noconfirm --onefile --windowed --name "FiveM Map Collision Finder" app.py
if errorlevel 1 goto error

echo.
echo Done. Your app is here:
echo   dist\FiveM Map Collision Finder.exe
echo Copy that single file to any Windows PC and double-click it.
pause
exit /b 0

:error
echo.
echo Build failed. Make sure Python is installed and on your PATH.
pause
exit /b 1
