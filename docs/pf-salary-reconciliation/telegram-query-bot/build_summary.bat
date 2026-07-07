@echo off
REM ============================================================================
REM  Double-click to build the compact salary "exceptions" summary that the
REM  Telegram bot reads. Reads your reconciled *_Final_Complete.xlsx files and
REM  writes a tiny Salary_Exceptions_Summary.xlsx next to this .bat.
REM
REM  EDIT THE TWO PATHS BELOW to point at your real folders, then double-click.
REM  (Keep the quotes — the folder names have spaces.)
REM ============================================================================
cd /d "%~dp0"
pip install pandas openpyxl

python build_exceptions_summary.py ^
  --in "D:\Desktop Data\salary 25-26\CORRECTED SALARY 25-26 (M13 FINAL)_20260626_020401 (1)\CORRECTED SALARY 25-26 (M13 FINAL)_20260626_020401\ESI_WASHING_REALLOCATED" ^
  --in "D:\Desktop Data\21062026\desktop salary folder" ^
  --out "Salary_Exceptions_Summary"

echo.
echo ===== DONE - upload Salary_Exceptions_Summary.xlsx to Google Drive =====
pause
