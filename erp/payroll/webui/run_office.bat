@echo off
REM ============================================================
REM  ISPL Payroll — start in OFFICE mode (colleagues on the same
REM  network can open it from their own PCs).
REM
REM  Use run.bat instead if only THIS PC should reach the app.
REM  First run only: allow it through the firewall by running this
REM  file once as Administrator (right-click > Run as administrator).
REM ============================================================
cd /d "%~dp0"

if not exist erp.config.bat (
  echo Settings file missing. Run run.bat first to create it.
  pause
  exit /b
)
call erp.config.bat
set ERP_HOST=0.0.0.0
if "%PORT%"=="" set PORT=8000

REM one-time firewall rule (silently ignored if not admin / already added)
netsh advfirewall firewall show rule name="ISPL Payroll" >nul 2>&1
if errorlevel 1 (
  netsh advfirewall firewall add rule name="ISPL Payroll" dir=in action=allow ^
    protocol=TCP localport=%PORT% profile=private >nul 2>&1
  if errorlevel 1 (
    echo NOTE: could not add the firewall rule automatically.
    echo       Right-click this file and "Run as administrator" once.
    echo.
  ) else (
    echo Firewall rule added for port %PORT% ^(private networks^).
    echo.
  )
)

echo Installing dependencies (first run only)...
python -m pip install -r requirements.txt
echo Setting up the database (safe to repeat)...
python init_db.py
if errorlevel 1 ( echo Setup failed — check erp.config.bat & pause & exit /b )

echo.
echo ============================================================
echo  ISPL Payroll is starting in OFFICE mode.
echo.
echo  On THIS PC:            http://127.0.0.1:%PORT%
echo  Colleagues should use: http://IP-SHOWN-BELOW:%PORT%
echo.
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do echo    this PC's IP: %%a
echo.
echo  (Keep this window open. Close it to stop the app.)
echo ============================================================
python app.py
pause
