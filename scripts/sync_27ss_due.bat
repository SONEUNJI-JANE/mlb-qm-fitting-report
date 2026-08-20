@echo off
cd /d "%~dp0.."
set PYTHONPATH=.
".venv\Scripts\python.exe" -m src.service.mlb_qm_fitting_report.sync_27ss_due >> "%~dp0sync_27ss_due.log" 2>&1
