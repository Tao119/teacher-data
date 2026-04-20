@echo off
setlocal

set ROOT=%~dp0

echo Starting FastAPI backend...
start "API" cmd /k "cd /d %ROOT% && set PYTHONPATH=src;apps/api/src && .venv\Scripts\uvicorn teacher_data_api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir src --reload-dir apps/api/src"

timeout /t 2 /nobreak >nul

echo Starting Next.js frontend...
start "Web" cmd /k "cd /d %ROOT%\apps\web && npm run dev -- --hostname 0.0.0.0"

echo.
echo   API: http://localhost:8000
echo   Web: http://localhost:3000
echo.
echo Close the opened terminals to stop the servers.
