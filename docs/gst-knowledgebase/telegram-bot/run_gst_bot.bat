@echo off
REM ── GST-ONLY bot ────────────────────────────────────────────────────────
REM Keys come from keys.bat (git-ignored). To run this as a SEPARATE bot from
REM the salary one, give it its own token: make a copy of keys.bat named
REM keys_gst.bat with a different TELEGRAM_BOT_TOKEN, then change the line
REM below from "call keys.bat" to "call keys_gst.bat".

set BOT_MODE=gst
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
