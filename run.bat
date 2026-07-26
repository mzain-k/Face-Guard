@echo off
echo Starting FaceGuard...
cd /d %~dp0
call ..\faceguard-env\Scripts\python.exe main.py
pause