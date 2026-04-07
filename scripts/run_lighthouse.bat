@echo off
setlocal

powershell -ExecutionPolicy Bypass -File "%~dp0run_lighthouse.ps1"
if errorlevel 1 exit /b 1

echo [perf] completed successfully
