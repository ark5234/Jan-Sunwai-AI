@echo off
setlocal

if "%1"=="" (
  powershell -ExecutionPolicy Bypass -File "%~dp0release_rc1.ps1"
) else (
  powershell -ExecutionPolicy Bypass -File "%~dp0release_rc1.ps1" "%1"
)

if errorlevel 1 exit /b 1
