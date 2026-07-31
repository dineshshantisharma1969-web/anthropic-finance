@echo off
REM ============================================================
REM  ISPL Payroll — create a one-click Desktop shortcut.
REM
REM  Run this ONCE (double-click). It puts an "ISPL Payroll ERP"
REM  icon on your Desktop that launches the app. After that you
REM  never open this folder again — just double-click the icon.
REM
REM  Paths are passed to PowerShell via environment variables so
REM  spaces and ( ) in the folder name can't break anything.
REM ============================================================
setlocal
cd /d "%~dp0"

REM which launcher the shortcut should run: run.bat (this PC only)
REM or run_office.bat (colleagues on the LAN can reach it too).
set "LAUNCHER=run.bat"
if /i "%~1"=="office" set "LAUNCHER=run_office.bat"

set "ERP_TARGET=%~dp0%LAUNCHER%"
set "ERP_WORKDIR=%~dp0"
set "ERP_ICON=%SystemRoot%\System32\shell32.dll,167"
set "ERP_NAME=ISPL Payroll ERP"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$desk=[Environment]::GetFolderPath('Desktop'); $lnk=Join-Path $desk ($env:ERP_NAME + '.lnk'); $w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut($lnk); $s.TargetPath=$env:ERP_TARGET; $s.WorkingDirectory=$env:ERP_WORKDIR; $s.IconLocation=$env:ERP_ICON; $s.Description='Launch ISPL Payroll ERP'; $s.Save(); Write-Host ''; Write-Host ('Created: ' + $lnk)"

if errorlevel 1 (
  echo.
  echo Could not create the shortcut automatically.
  echo Tell Claude the message shown above.
) else (
  echo.
  echo Done!  Look for "ISPL Payroll ERP" on your Desktop.
  echo Double-click that icon any time to open the app —
  echo you never need to open this folder again.
)
echo.
pause
