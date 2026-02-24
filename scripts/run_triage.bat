@echo off
echo Running Automated Triage...
echo.

pushd "%~dp0.."
cd backend
call "..\venv\Scripts\activate.bat" 2>nul || call "..\.venv\Scripts\activate.bat" 2>nul
python automated_triage.py --dataset-dir sorted_dataset --output-dir triage_output --prune-ratio 0.15
popd

pause