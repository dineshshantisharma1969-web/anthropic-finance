@echo off
REM ── ISPL Assistant bot (GST + Salary) ───────────────────────────────────
REM Your keys live in keys.bat (git-ignored) — see keys.bat.example for setup.
REM Double-click this file to start the bot. Keep the window open while it runs.

cd /d "%~dp0"
if not exist keys.bat (
  echo.
  echo  ERROR: keys.bat not found.
  echo  Copy keys.bat.example to keys.bat and paste your real keys into it.
  echo.
  pause
  exit /b 1
)
call keys.bat
python -m pip install -q -r requirements.txt
python gst_bot.py
pause
