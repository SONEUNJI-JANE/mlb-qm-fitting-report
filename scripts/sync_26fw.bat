@echo off
cd /d "%~dp0.."
set PYTHONPATH=.
".venv\Scripts\python.exe" -m src.service.mlb_qm_fitting_report.sync_26fw >> "%~dp0sync_26fw.log" 2>&1
