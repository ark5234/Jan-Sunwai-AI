@echo off
echo Running Backend Integration Tests...
echo.

set PYTHONPATH=%CD%\backend
python backend/tests/test_api_integration.py

pause