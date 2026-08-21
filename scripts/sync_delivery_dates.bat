@echo off
cd /d "%~dp0.."
set PYTHONPATH=.
".venv\Scripts\python.exe" -m src.service.mlb_qm_fitting_report.sync_delivery_dates >> "%~dp0sync_delivery_dates.log" 2>&1
