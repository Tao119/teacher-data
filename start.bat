@echo off
setlocal EnableDelayedExpansion

set ROOT=%~dp0
REM 末尾のバックスラッシュを除去
if "%ROOT:~-1%"=="\" set ROOT=%ROOT:~0,-1%

echo Starting FastAPI backend...
set API_CMD=cd /d "%ROOT%" ^&^& set "PYTHONPATH=%ROOT%\src;%ROOT%\apps\api\src" ^&^& "%ROOT%\.venv\Scripts\uvicorn.exe" teacher_data_api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir "%ROOT%\src" --reload-dir "%ROOT%\apps\api\src"
start "Teacher Data API" cmd /k "%API_CMD%"

timeout /t 3 /nobreak >nul

echo Starting Next.js frontend...
set WEB_CMD=cd /d "%ROOT%\apps\web" ^&^& npx next dev --hostname 0.0.0.0
start "Teacher Data Web" cmd /k "%WEB_CMD%"

echo.
echo   API: http://localhost:8000
echo   Web: http://localhost:3000
echo.
echo ターミナルを閉じるとサーバーが停止します。
