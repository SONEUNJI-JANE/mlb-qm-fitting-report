@echo off
cd /d "%~dp0.."
set PYTHONPATH=.
echo Syncing 26FW fitting chart...
".venv\Scripts\python.exe" -m src.service.mlb_qm_fitting_report.sync_26fw
echo Syncing 27SS DUE dates...
".venv\Scripts\python.exe" -m src.service.mlb_qm_fitting_report.sync_27ss_due
echo Syncing sourcing delivery dates...
".venv\Scripts\python.exe" -m src.service.mlb_qm_fitting_report.sync_delivery_dates
echo.
echo Done. Refresh the dashboard (Ctrl+Shift+R) to see the update.
pause
