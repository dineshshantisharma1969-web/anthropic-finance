@echo off
REM ============================================================
REM  ISPL Payroll — start the app (Windows). Double-click to run.
REM ============================================================
cd /d "%~dp0"

if not exist erp.config.bat (
  echo First-time setup.
  copy erp.config.example.bat erp.config.bat >nul
  echo Created erp.config.bat — opening it now.
  echo Fill in your database details, SAVE, close Notepad, then run this again.
  notepad erp.config.bat
  pause
  exit /b
)

call erp.config.bat

echo Installing dependencies (first run only)...
python -m pip install -r requirements.txt

echo Setting up the database (safe to repeat)...
python init_db.py
if errorlevel 1 ( echo Setup failed — check your database details in erp.config.bat & pause & exit /b )

echo.
echo ============================================================
echo  ISPL Payroll is starting.
echo  Open this in your browser:  http://127.0.0.1:8000
echo  (Keep this window open. Close it to stop the app.)
echo ============================================================
python app.py
pause
