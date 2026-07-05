@echo off
REM ── SALARY-ONLY bot ─────────────────────────────────────────────────────
REM Keys come from keys.bat (git-ignored). To run this as a SEPARATE bot from
REM the GST one, give it its own token: make a copy of keys.bat named
REM keys_salary.bat with a different TELEGRAM_BOT_TOKEN, then change the line
REM below from "call keys.bat" to "call keys_salary.bat".

set BOT_MODE=salary
cd /d "%~dp0"
if not exist keys.bat (
  echo ERROR: keys.bat not found. Copy keys.bat.example to keys.bat and add your keys.
  pause
  exit /b 1
)
call keys.bat
python -m pip install -q -r requirements.txt
python gst_bot.py
pause
