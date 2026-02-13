@echo off
echo Running Backend Integration Tests...
echo.

pushd "%~dp0.."
echo Project root: %CD%

set PYTHONPATH=%CD%\backend
python backend/tests/test_api_integration.py

pause