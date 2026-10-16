@echo off
chcp 65001 >nul
set "TARGET=%~dp0start_bridge.bat"
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\waveview-bridge.bat"
> "%LNK%" echo @echo off
>> "%LNK%" echo start "웨이브뷰 MT5 브리지" /min cmd /c "%TARGET%"
echo 등록했습니다. 이제 윈도우를 켜면 브리지가 자동으로 실행됩니다.
echo 해제하려면 다음 파일을 지우세요: %LNK%
pause
