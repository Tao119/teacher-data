@echo off
setlocal
set ROOT=%~dp0
if "%ROOT:~-1%"=="\" set ROOT=%ROOT:~0,-1%

echo === teacher-data セットアップ ===
echo.

REM .envがなければ作成
if not exist "%ROOT%\.env" (
    copy "%ROOT%\.env.example" "%ROOT%\.env" >nul
    echo .env を作成しました。
) else (
    echo .env は既に存在します。
)

echo.
echo APIキーを入力してください。
echo.

set /p OPENAI_KEY="OPENAI_API_KEY (sk-...): "
set /p GOOGLE_KEY="GOOGLE_API_KEY (AIza...): "

(
echo OPENAI_API_KEY=%OPENAI_KEY%
echo GOOGLE_API_KEY=%GOOGLE_KEY%
echo LANGUAGE=ja
echo CONCURRENCY=2
echo OUTPUT_DIR=output
echo CACHE_DIR=.cache
) > "%ROOT%\.env"

echo.
echo .env を保存しました。
echo.

echo Python依存をインストール中...
cd /d "%ROOT%"
uv sync
if errorlevel 1 (
    echo.
    echo [エラー] uv が見つかりません。
    echo https://docs.astral.sh/uv/getting-started/installation/ からインストールしてください。
    pause
    exit /b 1
)
echo.

echo フロントエンドをインストール中...
cd /d "%ROOT%\apps\web"
npm install
if errorlevel 1 (
    echo.
    echo [エラー] npm が見つかりません。Node.js をインストールしてください。
    pause
    exit /b 1
)
cd /d "%ROOT%"
echo.

echo === セットアップ完了 ===
echo start.bat で起動できます。
echo.
pause
