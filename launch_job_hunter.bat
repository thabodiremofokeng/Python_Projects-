@echo off
title Job Hunter - Auto Application System
cd /d "C:\Thabo Documents\2025 Projects\Auto application"

echo.
echo  ========================================
echo   🚀 Job Hunter - Auto Application System
echo  ========================================
echo.
echo  Starting your automated job application system...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if the main script exists
if not exist "quick_launch.py" (
    echo ❌ quick_launch.py not found in current directory
    echo Please make sure you're in the correct project folder
    pause
    exit /b 1
)

REM Launch the application
echo ✅ Launching Job Hunter application...
python quick_launch.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo ❌ Application encountered an error
    pause
)
