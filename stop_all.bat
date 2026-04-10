@echo off
TITLE AI Chatbot Stopper

REM Check for Administrator privileges
NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM Change to script directory
cd /d "%~dp0"

echo ==================================================
echo      Self-Hosted AI Chatbot - Stop All Services
echo ==================================================
echo.

REM Stop all Docker containers via docker-compose
echo Stopping all Docker services...
cd /d "%~dp0infra"
docker-compose down

echo.
echo ==================================================
echo      All services have been stopped.
echo ==================================================
echo.
pause >nul
