@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set PYTHONPATH=.
echo [26FW 피팅현황 동기화 중...]
".venv\Scripts\python.exe" -m src.service.mlb_qm_fitting_report.sync_26fw
echo [27SS DUE 동기화 중...]
".venv\Scripts\python.exe" -m src.service.mlb_qm_fitting_report.sync_27ss_due
echo [소싱 납기일자 동기화 중...]
".venv\Scripts\python.exe" -m src.service.mlb_qm_fitting_report.sync_delivery_dates
echo.
echo 완료! 대시보드에서 새로고침(Ctrl+Shift+R)하면 반영돼있음.
pause
