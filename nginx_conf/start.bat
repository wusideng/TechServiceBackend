@echo off
setlocal

:: Set Nginx path - Please modify according to your actual installation path
set NGINX_PATH=C:\nginx

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Please run this script as administrator!
    pause
    exit /b 1
)

:: Display menu
:MENU
cls
echo Nginx Control Script
echo ===================
echo 1. Start Nginx
echo 2. Stop Nginx
echo 3. Reload Configuration
echo 4. Check Nginx Status
echo 5. Test Configuration File
echo 6. Exit
echo.

set /p choice=Please select an operation (1-6): 

if "%choice%"=="1" goto START
if "%choice%"=="2" goto STOP
if "%choice%"=="3" goto RELOAD
if "%choice%"=="4" goto STATUS
if "%choice%"=="5" goto TEST
if "%choice%"=="6" goto END

echo Invalid selection, please try again
timeout /t 2 >nul
goto MENU

:START
echo Starting Nginx...
cd /d %NGINX_PATH%
start nginx
echo Nginx started
timeout /t 2 >nul
goto MENU

:STOP
echo Stopping Nginx...
cd /d %NGINX_PATH%
nginx -s stop
echo Nginx stopped
timeout /t 2 >nul
goto MENU

:RELOAD
echo Reloading Nginx configuration...
cd /d %NGINX_PATH%
nginx -s reload
echo Configuration reloaded
timeout /t 2 >nul
goto MENU

:STATUS
echo Checking Nginx status...
tasklist /fi "imagename eq nginx.exe"
echo.
echo If you see nginx.exe process, Nginx is running
pause
goto MENU

:TEST
echo Testing Nginx configuration...
cd /d %NGINX_PATH%
nginx -t
pause
goto MENU

:END
echo Thank you for using!
exit /b 0