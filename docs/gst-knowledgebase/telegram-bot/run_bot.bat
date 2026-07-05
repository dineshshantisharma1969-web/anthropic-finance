@echo off
REM ── GST Law Telegram Bot — Windows starter ──────────────────────────────
REM 1) Edit the two lines below with your real keys (keep this file private!)
REM 2) Double-click this file. A console window stays open while the bot runs.

set TELEGRAM_BOT_TOKEN=PASTE-YOUR-BOTFATHER-TOKEN-HERE
set ANTHROPIC_API_KEY=PASTE-YOUR-ANTHROPIC-KEY-HERE
REM Access control: comma-separated Telegram IDs allowed to use this bot.
REM Leave blank = open to anyone. Each teammate sends /myid to get their ID.
set ALLOWED_USER_IDS=

cd /d "%~dp0"
python -m pip install -q -r requirements.txt
python gst_bot.py
pause
