@echo off
REM ============================================================
REM  ISPL Payroll — your local settings.
REM  1. Copy this file to  erp.config.bat
REM  2. Fill in your database details below and save.
REM  (erp.config.bat is git-ignored, so your password stays local.)
REM ============================================================

REM --- Your Postgres / Supabase connection (one line) ---
set ERP_DB=host=YOUR_HOST port=5432 user=YOUR_USER password=YOUR_PASSWORD dbname=postgres

REM --- A long random string that signs login cookies (make one up) ---
set ERP_SECRET=change-this-to-a-long-random-string-xyz123

REM --- First admin login (you'll set the password on first run) ---
set ERP_ADMIN_USER=dinesh

REM --- Where uploaded files are kept on this PC (optional) ---
set ERP_UPLOAD_DIR=%~dp0uploads
