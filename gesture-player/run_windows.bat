@echo off
setlocal
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Run setup_windows.bat first.
 pause
 exit /b 1
)
.venv\Scripts\python.exe main.py gui
if errorlevel 1 pause
