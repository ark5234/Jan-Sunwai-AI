@echo off
setlocal

pushd "%~dp0.."
set PYTHONPATH=%CD%\backend

echo [resilience] running resilience/security pytest suite
python -m pytest backend/tests/test_resilience_security.py backend/tests/test_api_matrix.py -q
if errorlevel 1 (
  popd
  exit /b 1
)

echo [resilience] PASS
popd
