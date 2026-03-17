@echo off
title Network Adapter Tweaker
cd /d "%~dp0"

:: Check Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install from python.org
    pause
    exit /b 1
)

:: Install customtkinter if missing
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo [*] Installing customtkinter...
    pip install customtkinter --quiet
)

:: Run as admin
python main.pyw
