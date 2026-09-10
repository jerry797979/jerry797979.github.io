@echo off
rem 지오테스 정보 글 자동 발행 — 작업 스케줄러가 매일 오전 10시 40분에 부릅니다.
rem 하루 2편. 편수를 바꾸려면 맨 아래 숫자만 고치면 됩니다.
rem
rem 파이썬 경로를 박아 둔 이유: 작업 스케줄러는 사람이 쓰는 것과 PATH 가 달라
rem "python 을 찾을 수 없음"으로 조용히 죽는 일이 있습니다.
rem
rem git 경로도 넣어 둡니다. daily_post.py 가 저장소에 커밋·푸시를 합니다.
chcp 65001 >nul
cd /d C:\Users\marke\Desktop\bitwave
set "PATH=C:\Program Files\Git\cmd;%PATH%"
set PYTHONIOENCODING=utf-8
"C:\Users\marke\AppData\Local\Programs\Python\Python314\python.exe" "C:\Users\marke\Desktop\bitwave\_tools\daily_post.py" 2
