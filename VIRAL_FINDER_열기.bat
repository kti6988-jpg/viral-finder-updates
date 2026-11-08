@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo VIRAL FINDER - 로컬 검색 엔진 준비 중...
py -3.15 -m pip --version >nul 2>&1
if errorlevel 1 (
  echo Python pip를 찾을 수 없습니다. Python 설치에서 pip를 활성화해 주세요.
  pause
  exit /b 1
)
py -3.15 -m pip install --disable-pip-version-check --quiet --upgrade yt-dlp
if errorlevel 1 (
  echo yt-dlp 설치 실패. 인터넷 연결과 Python pip를 확인해 주세요.
  pause
  exit /b 1
)
start "VIRAL FINDER local search" /min py -3.15 updater_server.py
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8765/index.html"
