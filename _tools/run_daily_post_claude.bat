@echo off
rem Ziotes daily post - write with Claude Code (2026-09-19). To go back to Gemini, point the task at run_daily_post.bat
chcp 65001 >nul
cd /d C:\Users\marke\Desktop\bitwave
set "PATH=C:\Program Files\Git\cmd;C:\Program Files\nodejs;%PATH%"
set PYTHONIOENCODING=utf-8
"C:\Users\marke\AppData\Local\Programs\Python\Python314\python.exe" "C:\Users\marke\Desktop\bitwave\_tools\daily_post_claude.py" 2
