@echo off
setlocal

cd /d "%~dp0.."
python scripts\run_notification_chain_test.py
