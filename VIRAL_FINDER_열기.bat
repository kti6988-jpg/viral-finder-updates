@echo off
chcp 65001 >nul
cd /d "%~dp0"
title VIRAL FINDER 2.0.1 - Launcher
echo VIRAL FINDER 2.0.1
where py
if errorlevel 1 (echo Python Launcher를 찾을 수 없습니다.& pause & exit /b 1)
echo yt-dlp 설치 중...
py -3.15 -m pip install --user --upgrade yt-dlp
if errorlevel 1 (echo Python 3.15 설치 실패. 기본 Python으로 재시도합니다.& py -m pip install --user --upgrade yt-dlp & if errorlevel 1 (echo 설치 실패. 오류 화면을 보내주세요.& pause & exit /b 1) & set PYRUN=py) else (set PYRUN=py -3.15)
%PYRUN% -c "import yt_dlp; print('yt-dlp OK:', yt_dlp.version.__version__)"
if errorlevel 1 (echo yt-dlp import 실패.& pause & exit /b 1)
start "VIRAL FINDER Server" /min cmd /c "%PYRUN% updater_server.py"
timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:8765/index.html"
echo 브라우저를 열었습니다.
