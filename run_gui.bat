@echo off
title IM-Benchmark-Lab GUI Launcher
cd /d "%~dp0"
echo =====================================================================
echo   IM-Benchmark-Lab - Influence Maximization Research Platform
echo   Launching CustomTkinter Desktop GUI...
echo =====================================================================

python "%~dp0src\im_research\gui\app.py"
if %errorlevel% neq 0 (
    echo.
    echo [INFO] Default python returned non-zero exit code.
    echo Trying Windows Python 3.14 directly...
    "C:\Users\LENOVO\AppData\Local\Python\pythoncore-3.14-64\python.exe" "%~dp0src\im_research\gui\app.py"
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to launch GUI.
        pause
    )
)

