@echo off
setlocal
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist logs mkdir logs
python -c "import sys,struct; assert sys.version_info[:3]==(3,13,2) and struct.calcsize('P')==8, 'Install Python 3.13.2 x64'" > logs\setup.log 2>&1
if errorlevel 1 goto fail
if not exist .venv\Scripts\python.exe python -m venv .venv >> logs\setup.log 2>&1
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements-lock.txt >> logs\setup.log 2>&1
if errorlevel 1 goto fail
.venv\Scripts\python.exe main.py prepare >> logs\setup.log 2>&1
if errorlevel 1 goto fail
.venv\Scripts\python.exe main.py check >> logs\setup.log 2>&1
if errorlevel 1 goto fail
echo Setup complete. Run run_windows.bat
exit /b 0
:fail
type logs\setup.log
echo Setup failed. See logs\setup.log
pause
exit /b 1
