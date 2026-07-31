@echo off
REM ============================================================
REM  ISPL Payroll — write erp.config.bat for you (no Notepad).
REM
REM  Double-click this, answer the questions, done. It creates a
REM  correctly-formatted erp.config.bat in this folder, then you
REM  just run run.bat (or the Desktop icon).
REM
REM  Safe to re-run any time — it overwrites the old config.
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo  === ISPL Payroll - database setup ===
echo.
echo  From Supabase: Connect ^> Session pooler, you get a line like
echo  postgresql://USER:PASSWORD@HOST:5432/postgres
echo.

set "DBHOST=aws-1-ap-northeast-2.pooler.supabase.com"
set "DBUSER=postgres.rgfhqghwkiqwhwxjatsc"

set /p IN_HOST="  Host [press Enter for %DBHOST%]: "
if not "%IN_HOST%"=="" set "DBHOST=%IN_HOST%"

set /p IN_USER="  User [press Enter for %DBUSER%]: "
if not "%IN_USER%"=="" set "DBUSER=%IN_USER%"

:askpw
set "DBPW="
set /p DBPW="  Password (letters and numbers only): "
if "%DBPW%"=="" (
  echo   Password cannot be empty.
  goto askpw
)

> erp.config.bat (
  echo @echo off
  echo set ERP_DB=host=%DBHOST% port=5432 user=%DBUSER% password=%DBPW% dbname=postgres
  echo set ERP_SECRET=ispl-payroll-secret-2026-x7k9m2
  echo set ERP_ADMIN_USER=dinesh
  echo set ERP_UPLOAD_DIR=%%~dp0uploads
)

echo.
echo  Wrote erp.config.bat in this folder.
echo.
choice /c YN /m "  Start the app now"
if errorlevel 2 goto done
call run.bat
goto :eof

:done
echo  OK - double-click run.bat (or the Desktop icon) when ready.
pause
