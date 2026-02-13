@echo off
echo Running Automated Triage...
echo.

pushd "%~dp0..\backend"
python automated_triage.py --dataset-dir sorted_dataset --output-dir triage_output --prune-ratio 0.15 --clip-min-conf 0.45 --clip-min-margin 0.08
popd

pause
