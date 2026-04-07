@echo off
setlocal

powershell -ExecutionPolicy Bypass -File "%~dp0simulate_clean_deploy.ps1"
if errorlevel 1 exit /b 1
