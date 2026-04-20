@echo off
setlocal EnableDelayedExpansion
set ROOT=%~dp0
if "%ROOT:~-1%"=="\" set ROOT=%ROOT:~0,-1%

echo === teacher-data セットアップ ===
echo.

REM 既存 .env から APIキーを読み取る
set EXISTING_OPENAI=
set EXISTING_GOOGLE=
if exist "%ROOT%\.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%ROOT%\.env") do (
        if "%%A"=="OPENAI_API_KEY" set EXISTING_OPENAI=%%B
        if "%%A"=="GOOGLE_API_KEY" set EXISTING_GOOGLE=%%B
    )
)

REM 両キーが揃っていればスキップ
if not "!EXISTING_OPENAI!"=="" if not "!EXISTING_GOOGLE!"=="" (
    echo .env にAPIキーが設定済みです。スキップします。
    echo   OPENAI_API_KEY: !EXISTING_OPENAI:~0,8!...
    echo   GOOGLE_API_KEY: !EXISTING_GOOGLE:~0,8!...
    goto :install
)

echo APIキーを入力してください。
echo.

set OPENAI_KEY=!EXISTING_OPENAI!
set GOOGLE_KEY=!EXISTING_GOOGLE!

if "!OPENAI_KEY!"=="" set /p OPENAI_KEY="OPENAI_API_KEY (sk-...): "
if "!GOOGLE_KEY!"=="" set /p GOOGLE_KEY="GOOGLE_API_KEY (AIza...): "

(
echo OPENAI_API_KEY=!OPENAI_KEY!
echo GOOGLE_API_KEY=!GOOGLE_KEY!
echo LANGUAGE=ja
echo CONCURRENCY=2
echo OUTPUT_DIR=output
echo CACHE_DIR=.cache
) > "%ROOT%\.env"

echo.
echo .env を保存しました。
echo.

:install

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

echo ffmpeg を確認中...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo.
    echo [警告] ffmpeg が見つかりません。音声処理に必要です。
    echo   winget install ffmpeg  または
    echo   https://ffmpeg.org/download.html からインストールしてください。
    echo   インストール後、Windowsを再起動してから start.bat を実行してください。
    echo.
) else (
    echo   ffmpeg OK
)
echo.

echo === セットアップ完了 ===
echo start.bat で起動できます。
echo.
pause
