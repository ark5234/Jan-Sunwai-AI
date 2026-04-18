@echo off
setlocal

cd /d "%~dp0.."
python scripts\run_cookie_smoke_test.py

set EXITCODE=%ERRORLEVEL%
endlocal & exit /b %EXITCODE%
