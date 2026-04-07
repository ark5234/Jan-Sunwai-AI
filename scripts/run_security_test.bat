@echo off
setlocal

pushd "%~dp0.."
set PYTHONPATH=%CD%\backend

echo [security] running automated security-focused pytest suites
python -m pytest backend/tests/test_resilience_security.py backend/tests/test_notification_chain.py backend/tests/test_auth_permissions.py -q
if errorlevel 1 (
  popd
  exit /b 1
)

echo [security] automated checks passed
popd
