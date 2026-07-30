@echo off
REM ============================================================
REM  ISPL monthly payroll pipeline — Drive folder -> clean CSV -> ERP.
REM
REM  Usage:
REM    run_month.bat            (processes the PREVIOUS calendar month)
REM    run_month.bat 2026-06    (processes a specific month)
REM
REM  Expects the month's inputs in  %DRIVE_BASE%\<YYYY-MM>\ :
REM    - salary sheet  (*salary*.xlsx / *FULL_monthly*.xlsx)
REM    - ECR PF files  (FORMAT*.xlsx — one per client)
REM    - ESI / Future  (*ESIC*.xlsx / *FUTURE*.xlsx)
REM  Writes <Mon>_CLEAN.csv + <Mon>_RULES_OUTCOME.csv into the same
REM  folder and loads the month straight into the payroll ERP.
REM ============================================================
cd /d "%~dp0"

REM --- EDIT THIS ONCE: your Google Drive synced base folder -----------
set DRIVE_BASE=G:\My Drive\SALARY DATA 2026-27

REM --- DB connection comes from the ERP app's own config --------------
call "%~dp0..\..\erp\payroll\webui\erp.config.bat"

if "%~1"=="" (
  for /f %%i in ('powershell -NoProfile -Command "(Get-Date).AddMonths(-1).ToString('yyyy-MM')"') do set MONTH=%%i
) else (
  set MONTH=%~1
)

echo Processing month %MONTH%  from  "%DRIVE_BASE%\%MONTH%"
python month_pipeline.py --folder "%DRIVE_BASE%\%MONTH%" --month %MONTH% --load
if errorlevel 1 (
  echo.
  echo PIPELINE STOPPED — see messages above. Nothing was loaded into the ERP.
) else (
  echo.
  echo %MONTH% is reconciled, validated and loaded into the ERP.
)
pause
