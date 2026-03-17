@echo off
title Build NATweaker.exe — by Bootstep (Protected)
cd /d "%~dp0"

echo ==================================================
echo   Network Adapter Tweaker — Protected Build
echo   by Bootstep
echo ==================================================
echo.

where python >nul 2>&1 || (echo [ERROR] Python not found! & pause & exit /b 1)

:: Install deps
echo [*] Installing build tools...
pip install pyinstaller tinyaes --quiet 2>nul

:: Generate random encryption key for .pyc files
:: This encrypts all bytecode inside the exe — prevents pyinstxtractor
set "PYIKEY=B00tSt3pNATw3ak!"

echo [*] Building with bytecode encryption...
echo     Key: %PYIKEY% (encrypts .pyc inside exe)
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --name "NATweaker" ^
    --key "%PYIKEY%" ^
    --add-data "adapter.py;." ^
    --add-data "guard.py;." ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --exclude-module unittest ^
    --exclude-module test ^
    --exclude-module pdb ^
    --exclude-module doctest ^
    --exclude-module pydoc ^
    --exclude-module tkinter.test ^
    --exclude-module lib2to3 ^
    --exclude-module xmlrpc ^
    --strip ^
    --noupx ^
    main.pyw

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo.
    echo If --key fails, install tinyaes:
    echo   pip install tinyaes
    echo.
    pause
    exit /b 1
)

:: Clean build artifacts
rd /s /q build 2>nul
del /q *.spec 2>nul

echo.
echo ==================================================
echo   [OK] Build successful!
echo   Output: dist\NATweaker.exe
echo ==================================================
echo.
echo Protection layers:
echo   1. Bytecode encrypted (AES) — pyinstxtractor = gibberish
echo   2. Anti-debug heartbeat — kills on debugger detect
echo   3. Anti-decompile — blocks uncompyle6/decompyle3
echo   4. Anti-tamper — detects file modification
echo   5. Anti-process — detects RE tools running
echo   6. Code scramble — co_filename overwritten
echo   7. Import blocker — blocks decompiler modules
echo   8. Anti-hook — detects API hooking
echo.
echo Run as Administrator for full functionality.
pause
