@echo off
title Docker Manage - Self-Hosted Generative AI Chatbot
:menu
cls
echo =======================================================
echo     Self-Hosted Generative AI Chatbot - Docker Menu
echo =======================================================
echo.
echo [1] Start the project (Run in background)
echo [2] Stop the project
echo [3] Restart the project
echo [4] View Logs
echo [5] Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto rebuild
if "%choice%"=="5" goto logs
if "%choice%"=="6" goto exit

echo Invalid choice. Please try again.
pause
goto menu

:start
echo.
echo Starting the project via docker-compose...
docker-compose up -d
echo.
echo Opening browser tabs...
start chrome "http://localhost:5173"
start chrome "http://localhost:5174"
start chrome "http://localhost:8000/docs"
echo.
pause
goto menu

:stop
echo.
echo Stopping the project via docker-compose...
docker-compose down
echo.
pause
goto menu

:restart
echo.
echo Restarting the project...
docker-compose restart
echo.
pause
goto menu

:rebuild
echo.
echo Rebuilding and updating the project...
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo.
echo Opening browser tabs...
start chrome "http://localhost:5173"
start chrome "http://localhost:5174"
start chrome "http://localhost:8000/docs"
echo.
pause
goto menu

:logs
echo.
echo Press Ctrl+C to exit log view...
docker-compose logs -f
pause
goto menu

:exit
exit
