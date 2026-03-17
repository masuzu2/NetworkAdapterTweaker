@echo off
title Network Adapter Tweaker
cd /d "%~dp0"
where python >nul 2>&1 || (echo Python not found! & pause & exit /b 1)
python main.pyw
