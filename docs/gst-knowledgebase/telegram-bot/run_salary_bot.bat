@echo off
REM ── SALARY-ONLY Telegram bot ────────────────────────────────────────────
REM Answers ISPL salary/PF/ESI reconciliation, wage-code & Labour-Code questions only.
REM Needs its OWN bot token from @BotFather (a DIFFERENT bot from the GST one).

set BOT_MODE=salary
set TELEGRAM_BOT_TOKEN=PASTE-YOUR-SALARY-BOT-TOKEN-HERE
set ANTHROPIC_API_KEY=PASTE-YOUR-ANTHROPIC-KEY-HERE

cd /d "%~dp0"
python -m pip install -q -r requirements.txt
python gst_bot.py
pause
