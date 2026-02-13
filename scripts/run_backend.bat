@echo off
echo Starting Jan-Sunwai AI Backend...
pushd "%~dp0.."
echo Project root: %CD%

set PYTHONPATH=%CD%\backend;%CD%
python -m uvicorn backend.main:app --reload

pause
