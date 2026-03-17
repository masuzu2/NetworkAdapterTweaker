@echo off
title Build NATweaker.exe
cd /d "%~dp0"
where python >nul 2>&1 || (echo Python not found! & pause & exit /b 1)
pip install pyinstaller --quiet
echo Building...
pyinstaller --noconfirm --onefile --windowed --name "NATweaker" --add-data "adapter.py;." main.pyw
echo.
if exist "dist\NATweaker.exe" (echo [OK] dist\NATweaker.exe) else (echo [FAIL] Build failed)
pause
