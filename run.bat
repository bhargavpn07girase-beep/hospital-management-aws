@echo off
title Hospital Management System
echo ============================================================
echo   Starting Hospital Management System (Healthcare AWS)
echo   Local Web Interface: http://localhost:5000
echo   Default Admin: username: admin ^| password: admin123
echo ============================================================
echo.

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] An error occurred while starting the application.
    pause
)
