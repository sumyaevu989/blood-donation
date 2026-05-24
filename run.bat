@echo off
echo ==========================================
echo    Blood Donation System - Server Starter
echo ==========================================
echo.
echo [1/2] Checking and cleaning up Port 8000 (if already in use)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo Killing stuck process with PID %%a...
    taskkill /f /pid %%a >nul 2>&1
)

echo [2/2] Starting Django Development Server...
python manage.py runserver
