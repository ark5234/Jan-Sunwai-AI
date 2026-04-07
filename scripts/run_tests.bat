@echo off
setlocal

echo Running backend test suite...
echo.

pushd "%~dp0.."
echo Project root: %CD%

set PYTHONPATH=%CD%\backend
python -m pytest backend/tests -q
if errorlevel 1 goto :failed

echo.
echo Running frontend lint/build smoke...
pushd frontend
call npm run lint
if errorlevel 1 goto :failed
call npm run build
if errorlevel 1 goto :failed
popd

echo.
echo All checks passed.
goto :done

:failed
echo.
echo Test or build failed.
popd
exit /b 1

:done
popd

endlocal