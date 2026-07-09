@echo off
setlocal
set "PY=C:\Users\honghaoxiang\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"
cd /d "%~dp0"
"%PY%" server.py
pause
