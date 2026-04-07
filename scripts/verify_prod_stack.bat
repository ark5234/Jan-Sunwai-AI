@echo off
setlocal

powershell -ExecutionPolicy Bypass -File "%~dp0verify_prod_stack.ps1"
if errorlevel 1 exit /b 1
