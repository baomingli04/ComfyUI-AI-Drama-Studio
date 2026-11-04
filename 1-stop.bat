@echo off
rem ============================================================
rem  AICG platform - one-click stop
rem  Stops ONLY the platform's own services:
rem      8081 = frontend Vite, 8001 = backend Django, 3306 = MariaDB
rem  Port 8080 is NOT touched (it belongs to llama-server).
rem  Encoding: GBK / ANSI - do NOT re-save this file as UTF-8.
rem ============================================================
setlocal EnableDelayedExpansion

echo.
echo ================ AICG platform - stop ================
echo.

call :StopPort 8081 "Frontend Vite"
call :StopPort 8001 "Backend Django"
call :StopPort 3306 "Database MariaDB"

rem close the console windows left by the start script
for %%T in ("AICG-Frontend" "AICG-Backend" "AICG-Database") do (
    taskkill /FI "WINDOWTITLE eq %%~T*" /F >nul 2>&1
)

echo.
echo [verify] ports still listening:
set STILL=0
for %%P in (8081 8001 3306) do (
    netstat -ano | findstr ":%%P " | findstr "LISTENING" >nul
    if not errorlevel 1 (
        echo   port %%P STILL listening ^(admin rights needed?^)
        set STILL=1
    )
)
if "!STILL!"=="0" echo   all platform ports are free.

echo.
echo ================ Stop finished ================
echo  Restart: run start-platform.bat
echo  Note   : backend runs with --noreload; restart it after editing .py files.
echo  Note   : 8080 (llama-server) is left untouched on purpose.
echo.
pause
exit /b 0

:StopPort
set "PORT=%~1"
set "NAME=%~2"
set FOUND=0
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
    set FOUND=1
    echo   [%NAME%] port %PORT% -^> killing PID %%P
    taskkill /PID %%P /T /F >nul 2>&1
    if errorlevel 1 echo     WARNING: taskkill failed for PID %%P
)
if "!FOUND!"=="0" echo   [%NAME%] port %PORT% not running, skipped.
exit /b 0
