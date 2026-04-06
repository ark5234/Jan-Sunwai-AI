@echo off
setlocal

cd /d "%~dp0..\backend"
python -m pip install -r requirements-loadtest.txt
locust -f locustfile.py --host %1

if "%1"=="" (
  echo Tip: pass host URL as first argument. Example: run_load_test.bat http://localhost:8000
)
