@echo off
title Network Adapter Tweaker - Build
echo ============================================
echo   Network Adapter Tweaker - Auto Build
echo ============================================
echo.

:: --- Find Visual Studio vcvarsall.bat ---
set "VCVARS="

:: VS 2022 Community
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
    echo [OK] Found VS 2022 Community
    goto :found
)
:: VS 2022 Professional
if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat"
    echo [OK] Found VS 2022 Professional
    goto :found
)
:: VS 2022 Enterprise
if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat"
    echo [OK] Found VS 2022 Enterprise
    goto :found
)
:: VS 2019 Community
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARS=C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat"
    echo [OK] Found VS 2019 Community
    goto :found
)
:: VS 2019 Professional
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARS=C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build\vcvarsall.bat"
    echo [OK] Found VS 2019 Professional
    goto :found
)
:: VS Build Tools 2022
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARS=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
    echo [OK] Found VS 2022 Build Tools
    goto :found
)
if exist "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARS=C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
    echo [OK] Found VS 2022 Build Tools
    goto :found
)

:: Not found
echo [ERROR] Visual Studio not found!
echo.
echo Please install one of these (free):
echo   1. Visual Studio 2022 Community
echo      https://visualstudio.microsoft.com/downloads/
echo      Select "Desktop development with C++"
echo.
echo   2. Or just Build Tools (smaller):
echo      https://visualstudio.microsoft.com/visual-cpp-build-tools/
echo.
pause
exit /b 1

:found
echo.
echo [*] Setting up compiler environment...
call "%VCVARS%" x64 >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to initialize compiler
    pause
    exit /b 1
)
echo [OK] Compiler ready (x64)
echo.

:: --- Build ---
echo [*] Compiling...
cd /d "%~dp0src"

cl /nologo /EHsc /utf-8 /O2 /W3 ^
    main.cpp gui.cpp adapter.cpp ^
    /Fe:"..\NATweaker.exe" ^
    /link user32.lib gdi32.lib advapi32.lib comctl32.lib shell32.lib

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    cd /d "%~dp0"
    pause
    exit /b 1
)

:: Clean up .obj files
del /q *.obj >nul 2>&1
cd /d "%~dp0"

echo.
echo ============================================
echo   [OK] Build successful!
echo   Output: NATweaker.exe
echo ============================================
echo.
echo Run as Administrator for full functionality.
echo.
pause
