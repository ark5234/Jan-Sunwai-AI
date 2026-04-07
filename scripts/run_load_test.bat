@echo off
setlocal

cd /d "%~dp0..\backend"
set HOST=%1
if "%HOST%"=="" set HOST=http://localhost:8000

if "%USERS%"=="" set USERS=70
if "%SPAWN_RATE%"=="" set SPAWN_RATE=10
if "%DURATION%"=="" set DURATION=15m

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set STAMP=%%i
set OUT_DIR=..\reports\load\%STAMP%
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

python -m pip install -r requirements-loadtest.txt
python -m locust -f locustfile.py --host %HOST% --headless -u %USERS% -r %SPAWN_RATE% -t %DURATION% --html "%OUT_DIR%\locust-report.html" --csv "%OUT_DIR%\locust" --only-summary

echo [load-test] report generated at: %OUT_DIR%
