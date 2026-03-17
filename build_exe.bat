@echo off
title Build NATweaker.exe
cd /d "%~dp0"

echo ============================================
echo   Network Adapter Tweaker - Build EXE
echo ============================================
echo.

:: Check Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

:: Install deps
echo [*] Installing dependencies...
pip install customtkinter pyinstaller --quiet

:: Build
echo [*] Building EXE (this takes ~30 seconds)...
pyinstaller --noconfirm --onefile --windowed ^
    --name "NATweaker" ^
    --add-data "adapter.py;." ^
    --hidden-import customtkinter ^
    --icon NONE ^
    main.pyw

if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   [OK] Build successful!
echo   Output: dist\NATweaker.exe
echo ============================================
echo.
echo Run as Administrator for full functionality.
pause
