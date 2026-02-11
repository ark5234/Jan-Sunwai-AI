@echo off
echo Starting Jan-Sunwai AI Backend...
echo Ensure you are running this from the Project Root.
echo.

set PYTHONPATH=%CD%\backend;%CD%
python -m uvicorn backend.main:app --reload

pause
