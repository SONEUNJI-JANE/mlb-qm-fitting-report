@echo off
cd /d "C:\Users\AC1005\OneDrive - F&F\★JANE★\CODE\meeting_note"
set PYTHONPATH=.
".venv\Scripts\python.exe" src\service\mlb_qm_fitting_report\run_weekly.py
if errorlevel 1 exit /b 1
dcs-ai-cli app update mlb-qm-fitting-weekly --path src\output\dashboard
