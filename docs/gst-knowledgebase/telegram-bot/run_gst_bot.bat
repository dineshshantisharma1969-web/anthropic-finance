@echo off
REM ── GST-ONLY Telegram bot ───────────────────────────────────────────────
REM Answers GST law/rules/notifications questions only.
REM Needs its OWN bot token from @BotFather (a DIFFERENT bot from the salary one).

set BOT_MODE=gst
set TELEGRAM_BOT_TOKEN=PASTE-YOUR-GST-BOT-TOKEN-HERE
set ANTHROPIC_API_KEY=PASTE-YOUR-ANTHROPIC-KEY-HERE
REM Access control: comma-separated Telegram IDs allowed to use this bot.
REM Leave blank = open to anyone. Each teammate sends /myid to get their ID.
set ALLOWED_USER_IDS=

cd /d "%~dp0"
python -m pip install -q -r requirements.txt
python gst_bot.py
pause
