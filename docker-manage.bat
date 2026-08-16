@echo off
setlocal enabledelayedexpansion
title Docker Manage - Self-Hosted Generative AI Chatbot

REM LAN address of this machine, resolved once at startup.
REM
REM `ipconfig` is parsed rather than `hostname -I` (not a Windows thing) and
REM rather than hardcoding: the address changes with the network, and the whole
REM point of printing it is to have the one that is true right now. The first
REM IPv4 that is not loopback wins; on a machine with several adapters (Wi-Fi
REM plus a Docker or VPN virtual NIC) that is usually right, and option [8]
REM prints every candidate when it is not.
set "LAN_IP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    for /f "tokens=* delims= " %%b in ("%%a") do (
        if not defined LAN_IP if not "%%b"=="127.0.0.1" set "LAN_IP=%%b"
    )
)
if not defined LAN_IP set "LAN_IP=<no network adapter found>"

:menu
cls
echo =======================================================
echo     Self-Hosted Generative AI Chatbot - Docker Menu
echo =======================================================
echo.
echo [1] Start the project (Run in background)
echo [2] Stop the project
echo [3] Restart the project
echo [4] Rebuild the project
echo [5] View Logs
echo [6] Run database migrations
echo [7] Show URLs (local + network for phone/tablet)
echo [8] Enable phone/LAN access (adds this PC's IP to ALLOWED_HOSTS)
echo [9] RESET ALL DATA (destructive)
echo [0] Exit
echo.
set /p choice="Enter your choice (0-9): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto rebuild
if "%choice%"=="5" goto logs
if "%choice%"=="6" goto migrate
if "%choice%"=="7" goto urls
if "%choice%"=="8" goto lanaccess
if "%choice%"=="9" goto reset
if "%choice%"=="0" goto exit

echo Invalid choice. Please try again.
pause
goto menu

:showurls
echo.
echo  -----------------------------------------------------
echo    On this PC
echo  -----------------------------------------------------
echo      App     http://localhost:5173
echo      Admin   http://localhost:5174
echo      API     http://localhost:8000/docs
echo.
echo  -----------------------------------------------------
echo    On your phone / tablet  (same Wi-Fi as this PC)
echo  -----------------------------------------------------
echo      App     http://%LAN_IP%:5173
echo      Admin   http://%LAN_IP%:5174
echo      API     http://%LAN_IP%:8000/docs
echo  -----------------------------------------------------
echo.
exit /b

:start
echo.
echo Starting the project via docker-compose...
docker-compose up -d
call :showurls
echo Opening browser tabs...
start chrome "http://localhost:5173"
start chrome "http://localhost:5174"
echo.
pause
goto menu

:urls
cls
echo =======================================================
echo     Where the project is reachable
echo =======================================================
call :showurls
echo  If the phone URLs do not load:
echo.
echo    1. Phone and PC must be on the SAME Wi-Fi network.
echo       Guest networks and "client isolation" block this.
echo    2. Windows Firewall must allow ports 5173, 5174 and
echo       8000 on a Private network. The first time Docker
echo       binds them Windows shows a prompt - if you clicked
echo       "Cancel", allow them in Windows Defender Firewall.
echo    3. The backend rejects unknown host names by design.
echo       Run option [8] once to add %LAN_IP% to the allow
echo       list, otherwise the pages load but every API call
echo       fails with "Invalid host header".
echo.
echo  All detected IPv4 addresses on this PC:
ipconfig ^| findstr /c:"IPv4 Address"
echo.
pause
goto menu

:lanaccess
cls
echo =======================================================
echo     Enable phone / LAN access
echo =======================================================
echo.
if not exist ".env" (
    echo  No .env file found in this folder, so there is nothing
    echo  to edit. Create one first, then run this again.
    echo.
    pause
    goto menu
)
echo  The backend uses TrustedHostMiddleware, which refuses any
echo  request whose Host header is not on an allow list. That is
echo  a deliberate defence against Host-header poisoning, and it
echo  is why the app loads over Wi-Fi but every API call fails.
echo.
echo  This adds ONE line to your .env:
echo.
echo      ALLOWED_HOSTS=localhost,127.0.0.1,%LAN_IP%
echo.
echo  Only do this on a network you trust - it makes the API
echo  answer to this PC's LAN address, not just to localhost.
echo.
set /p lanconfirm="Add it and restart the backend? (y/N): "
if /i not "%lanconfirm%"=="y" (
    echo.
    echo Cancelled - .env was not changed.
    pause
    goto menu
)

REM Drop any existing ALLOWED_HOSTS line, then append the new one, so running
REM this twice (or after the IP changes) replaces rather than duplicates.
findstr /v /b /c:"ALLOWED_HOSTS=" .env > .env.tmp
echo ALLOWED_HOSTS=localhost,127.0.0.1,%LAN_IP%>> .env.tmp
move /y .env.tmp .env >nul
echo.
echo  .env updated. Restarting the backend so it re-reads it...
docker-compose up -d --force-recreate backend
call :showurls
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
call :showurls
pause
goto menu

:rebuild
echo.
echo Rebuilding and updating the project...
docker-compose down
docker-compose build --no-cache
docker-compose up -d
call :showurls
echo Opening browser tabs...
start chrome "http://localhost:5173"
start chrome "http://localhost:5174"
echo.
pause
goto menu

:logs
echo.
echo Press Ctrl+C to exit log view...
docker-compose logs -f
pause
goto menu

:migrate
echo.
echo Applying Alembic migrations to head...
echo (The backend also runs these on startup in production. This is for
echo  applying a new revision without a full restart.)
docker-compose exec backend alembic upgrade head
echo.
pause
goto menu

:reset
echo.
echo =======================================================
echo  WARNING - THIS DESTROYS ALL DATA. THERE IS NO UNDO.
echo =======================================================
echo.
echo  The following are deleted permanently:
echo.
echo    - Postgres      accounts, chats, subscriptions, usage
echo                    records, projects, and the platform
echo                    profile (your legal + company details)
echo    - Redis         sessions and cached history
echo    - ChromaDB      all RAG and project-knowledge vectors
echo    - Image storage every generated image file
echo.
echo  Schema is rebuilt from migrations on next start, and the
echo  default plans and admin user are re-seeded. Everything
echo  else is gone.
echo.
echo  NOTE: the Legal ^& Company details in the admin console
echo  are stored in Postgres and WILL be erased. Export or
echo  screenshot them first if they are already filled in.
echo.
set /p confirm="Type ERASE in capitals to proceed: "
if not "%confirm%"=="ERASE" (
    echo.
    echo Cancelled - nothing was deleted.
    pause
    goto menu
)
echo.
echo Stopping containers and removing named volumes...
REM `-v` removes the named volumes declared in docker-compose.yml:
REM postgres_data, redis_data, chromadb_data and backend_images.
REM Without it `down` leaves every one of them intact, which is why a
REM "reset" that only ran `down` then `up` appeared to change nothing.
docker-compose down -v
echo.
echo Starting fresh...
docker-compose up -d
echo.
echo Done. The backend runs migrations and re-seeds on startup;
echo give it a minute, then check option [5] for progress.
echo.
pause
goto menu

:exit
exit
