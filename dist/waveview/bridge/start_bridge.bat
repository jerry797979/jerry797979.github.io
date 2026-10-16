@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 이 설치되어 있지 않습니다. https://www.python.org 에서 설치하세요. 설치 화면에서 "Add python.exe to PATH" 를 꼭 체크하세요. & pause & exit /b)
echo MT5 연결 모듈을 확인하는 중...
python -m pip install --quiet --disable-pip-version-check MetaTrader5
python mt5_bridge.py
pause
