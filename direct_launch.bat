@echo off
title Job Hunter - Auto Application System
cd /d "C:\Thabo Documents\2025 Projects\Auto application"

echo.
echo  ========================================
echo   🚀 Job Hunter - Auto Application System
echo  ========================================
echo.
echo  🌐 Starting web interface with existing data...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Start the web app directly
echo ✅ Launching Job Hunter web interface...
python web/app.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo ❌ Application encountered an error
    pause
)
