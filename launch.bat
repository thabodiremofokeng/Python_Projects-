@echo off
title Auto Job Application System
color 0A

echo.
echo =============================================================
echo   AUTO JOB APPLICATION SYSTEM - QUICK LAUNCHER
echo =============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or later
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if we're in the right directory
if not exist "src" (
    echo ❌ Please run this script from the project root directory
    echo Expected to find 'src' folder here
    pause
    exit /b 1
)

echo ✅ Project directory confirmed
echo.

REM Show options
echo Choose launch option:
echo.
echo 1. 🚀 Full Launch (scrape jobs + web interface)
echo 2. ⚡ Quick Launch (interactive options)
echo 3. 🌐 Web Only (use existing data)
echo 4. 🧪 Test System
echo 5. 🧹 Clear Database
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo 🚀 Starting full unified launcher...
    python launch_app.py
) else if "%choice%"=="2" (
    echo.
    echo ⚡ Starting quick launcher...
    python quick_launch.py
) else if "%choice%"=="3" (
    echo.
    echo 🌐 Starting web interface only...
    python start_app.py
) else if "%choice%"=="4" (
    echo.
    echo 🧪 Running system tests...
    python test_real_scraping.py
    pause
) else if "%choice%"=="5" (
    echo.
    echo 🧹 Clearing database...
    python clear_database.py
    pause
) else (
    echo.
    echo ❌ Invalid choice. Please run the script again.
    pause
    exit /b 1
)

echo.
echo 👋 Application finished
pause
