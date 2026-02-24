@echo off
echo Starting Jan-Sunwai AI Backend...
pushd "%~dp0.."
echo Project root: %CD%

set PYTHONPATH=%CD%\backend;%CD%
call .venv\Scripts\activate.bat
python -m uvicorn backend.main:app --reload

pause
