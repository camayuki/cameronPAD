@echo off
REM CameronPAD Server Startup Script
REM Starts the FastAPI server on 127.0.0.1:8000

echo ========================================
echo   Starting CameronPAD Server
echo ========================================
echo.
echo Server will be available at:
echo   http://127.0.0.1:8000
echo.
echo Press CTRL+C to stop the server
echo ========================================
echo.

cd /d "%~dp0"
py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000

pause
