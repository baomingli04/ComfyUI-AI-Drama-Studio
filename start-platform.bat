@echo off
rem ============================================================
rem  AICG platform - one-click start (database / backend / frontend)
rem  Encoding: GBK / ANSI - do NOT re-save this file as UTF-8.
rem ============================================================
setlocal EnableDelayedExpansion

set MYSQL_BIN=D:\MariaDB\mariadb-11.4.13-winx64\bin
set MYSQL_INI=D:\MariaDB\mariadb-11.4.13-winx64\my.ini
set BE_DIR=%~dp0backend
set FE_DIR=%~dp0frontend

echo.
echo ================ AICG platform - start ================
echo.

rem ---------- 0. preflight ----------
set ERR=0
if not exist "%MYSQL_BIN%\mysqld.exe" (echo [PREFLIGHT] MISSING: mysqld.exe & set ERR=1)
if not exist "%MYSQL_INI%" (echo [PREFLIGHT] MISSING: my.ini & set ERR=1)
if not exist "%BE_DIR%\manage.py" (echo [PREFLIGHT] MISSING: manage.py & set ERR=1)
if not exist "%BE_DIR%\.venv\Scripts\python.exe" (echo [PREFLIGHT] MISSING: venv python & set ERR=1)
if not exist "%FE_DIR%\package.json" (echo [PREFLIGHT] MISSING: package.json & set ERR=1)
if "%ERR%"=="1" (
    echo [PREFLIGHT] FAILED - fix the paths above, then run again.
    pause
    exit /b 1
)
echo [PREFLIGHT] paths OK.

rem ---------- 1. MariaDB 3306 ----------
netstat -ano | findstr ":3306 " | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo [1/3] MariaDB 3306 already listening, skipped.
) else (
    echo [1/3] MariaDB not running, starting...
    start "AICG-Database" cmd /k "cd /d %MYSQL_BIN% && mysqld.exe --defaults-file=%MYSQL_INI% --console"
    call :WaitPort 3306 120 DB_OK
    if "!DB_OK!"=="1" (
        echo [1/3] Database ready.
    ) else (
        echo [1/3] ERROR: MariaDB did not open 3306 within 120s.
        echo       Read the real error in the "AICG-Database" window.
        pause
        exit /b 1
    )
)

rem ---------- 1.5 Apply Django migrations (best-effort, idempotent) ----------
echo [1.5/3] Applying Django migrations (best-effort)...
cd /d "%BE_DIR%"
.venv\Scripts\python.exe manage.py migrate --noinput
if not errorlevel 1 (
    echo [1.5/3] Migrations applied / already up to date.
) else (
    echo [1.5/3] WARNING: migrate reported errors - see output above.
    echo           backend may still work if tables were created via aicg.sql
)
cd /d "%~dp0"

rem ---------- 2. Backend Django 8001 ----------
netstat -ano | findstr ":8001 " | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo [2/3] Backend 8001 already listening, skipped.
    echo       NOTE: autoreload is on; .py changes reload automatically.
) else (
    echo [2/3] Backend not running, starting...
    start "AICG-Backend" cmd /k "cd /d %BE_DIR% && .venv\Scripts\python.exe manage.py runserver 0.0.0.0:8001"
    call :WaitPort 8001 60 BE_OK
    if "!BE_OK!"=="1" (
        echo [2/3] Backend ready.
        curl -s -m 5 --noproxy * -o nul http://127.0.0.1:8001/ >nul 2>&1
        if not errorlevel 1 (
            echo [2/3] Backend HTTP responded.
        ) else (
            echo [2/3] WARNING: port open but HTTP did not respond.
        )
    ) else (
        echo [2/3] ERROR: backend did not open 8001 within 60s.
        echo       Read the real error in the "AICG-Backend" window.
        pause
        exit /b 1
    )
)

rem ---------- 3. Frontend Vite ----------
rem Frontend is probed on 8081 ONLY.
rem Port 8080 belongs to llama-server: this script never starts anything on it
rem and never kills it.
netstat -ano | findstr ":8081 " | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo [3/3] Frontend already listening on 8081, skipped.
) else (
    echo [3/3] Frontend not running, starting npm run dev...
    start "AICG-Frontend" cmd /k "cd /d %FE_DIR% && npm run dev"
    call :WaitPort 8081 90 FE_OK
    if "!FE_OK!"=="1" (
        echo [3/3] Frontend ready on 8081.
    ) else (
        echo [3/3] ERROR: frontend did not open 8081 within 90s.
        echo       Read the real error in the "AICG-Frontend" window.
        pause
        exit /b 1
    )
)

echo.
echo ================ Start finished ================
echo  Frontend : http://127.0.0.1:8081/
echo  Backend  : http://127.0.0.1:8001/api/
echo.
pause
exit /b 0

:WaitPort
set "WP_PORT=%~1"
set "WP_MAX=%~2"
set "WP_OUT=%~3"
set %WP_OUT%=0
for /l %%i in (1,1,%WP_MAX%) do (
    netstat -ano | findstr ":%WP_PORT% " | findstr "LISTENING" >nul
    if not errorlevel 1 (
        set %WP_OUT%=1
        exit /b 0
    )
    set /a WP_TEN=%%i %% 10
    if "!WP_TEN!"=="0" echo       ... waiting for %WP_PORT% ^(%%i s of %WP_MAX% s^)
    ping -n 2 127.0.0.1 >nul
)
exit /b 0
