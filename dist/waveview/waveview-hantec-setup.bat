@echo off
chcp 65001 >nul
title 웨이브뷰 한텍 MT5 연결 설치
setlocal
set "WV=%LOCALAPPDATA%\WaveView"
set "SITE=https://jerry797979.github.io/waveview"
if not exist "%WV%" mkdir "%WV%"
echo.
echo  웨이브뷰 - 한텍 MT5 연결을 설치합니다. 창을 닫지 말고 기다려 주세요.
echo.

rem 1) 파이썬 찾기 (없으면 자동 설치)
set "PY="
for %%V in (313 312 311 310) do if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
if not defined PY (
  echo  [1/4] 파이썬을 설치하는 중입니다... 1~3분 걸립니다.
  curl -L -s -o "%TEMP%\wv-python.exe" https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe
  "%TEMP%\wv-python.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
  set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) else (
  echo  [1/4] 파이썬 확인 완료
)
if not exist "%PY%" (
  echo.
  echo  파이썬 설치에 실패했습니다. 인터넷 연결을 확인하고 다시 실행해 주세요.
  pause & exit /b 1
)
for %%F in ("%PY%") do set "PYW=%%~dpFpythonw.exe"

rem 2) MT5 연결 모듈
echo  [2/4] MT5 연결 모듈을 설치하는 중입니다...
"%PY%" -m pip install --quiet --disable-pip-version-check --upgrade MetaTrader5

rem 3) 연결 프로그램 받기
echo  [3/4] 연결 프로그램을 받는 중입니다...
curl -L -s -o "%WV%\mt5_bridge.py" "%SITE%/bridge/mt5_bridge.py"
if not exist "%WV%\mt5_bridge.py" (
  echo  연결 프로그램을 받지 못했습니다. 인터넷 연결을 확인하고 다시 실행해 주세요.
  pause & exit /b 1
)

rem 4) 화면 없이 실행 + 컴퓨터 켤 때 자동 실행
echo  [4/4] 자동 실행을 등록하는 중입니다...
> "%WV%\run-bridge.vbs" echo CreateObject("WScript.Shell").Run """%PYW%"" ""%WV%\mt5_bridge.py""", 0, False
copy /y "%WV%\run-bridge.vbs" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WaveView-Bridge.vbs" >nul
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe' OR Name='python.exe'\" | Where-Object { $_.CommandLine -like '*mt5_bridge.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>nul
wscript "%WV%\run-bridge.vbs"

echo.
echo  설치가 끝났습니다. 한텍 MT5 를 켜고 로그인해 두면 웨이브뷰가 자동으로 연결됩니다.
echo  (크롬이 '로컬 네트워크 접근'을 물으면 [허용]을 누르세요)
echo.
start "" "%SITE%/"
timeout /t 8 >nul
