@echo off
REM ============================================================================
REM  Double-click to build the compact salary "exceptions" summary that the
REM  Telegram bot reads. Reads your reconciled M13 FINAL / Final_Complete files
REM  and writes a tiny Salary_Exceptions_Summary.xlsx next to this .bat.
REM
REM  The two folder paths are set with SET below. If your folders move, edit the
REM  two SET lines (keep the quotes off — they're added automatically).
REM ============================================================================
cd /d "%~dp0"
pip install pandas openpyxl

set "FY2526=D:\Desktop Data\salary 25-26\CORRECTED SALARY 25-26 (M13 FINAL)_20260626_020401 (1)\CORRECTED SALARY 25-26 (M13 FINAL)_20260626_020401\ESI_WASHING_REALLOCATED"
set "APR26=D:\Desktop Data\21062026\desktop salary folder"

python build_exceptions_summary.py --in "%FY2526%" --in "%APR26%" --fy 2025 --out "Salary_Exceptions_Summary"

echo.
echo ===== DONE - upload Salary_Exceptions_Summary.xlsx to Google Drive =====
pause
