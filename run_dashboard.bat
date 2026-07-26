@echo off
echo Starting FaceGuard Dashboard...

start "FaceGuard Backend" cmd /k "cd /d %~dp0dashboard\backend && ..\..\..\..\faceguard-env\Scripts\python.exe -m uvicorn main:app --port 8000"

timeout /t 3

start "FaceGuard Frontend" cmd /k "cd /d %~dp0dashboard\frontend && npm start"

echo Dashboard starting at http://localhost:3000