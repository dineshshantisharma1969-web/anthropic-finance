<#
.SYNOPSIS
    Aligns REVISED_PF in the monthly M13_FINAL salary sheets with the EE share
    actually deposited per the EPFO ECR challan files (books), for FY 2025-26 —
    implementing the golden rules and mandatory checks of the
    pf-salary-reconciliation skill (SKILL.md, consolidated v4 + M1/M2 patches).

.DESCRIPTION
    Only UANs whose current sheet total differs from the ECR EE amount by more
    than 1 rupee are touched; everything else is left byte-for-byte alone.
    For every such UAN (April..March):

      1. PARSE BOOKS — reads all ECR text files under the month's -EcrRoot folder
         and totals the EE share per UAN (the "books" / statutory-filing figure).

      2. MULTI-SITE PRIMARY (Rule M1) — if the UAN has more than one row, the
         PRIMARY row is the one with the highest NORMALDAYS (days actually
         worked that month) — not simply the row already carrying PF. Every
         other row's existing PF (if any) is zeroed and parked into THAT row's
         own REVISED_OTHER_DEDUCTION, so that row's own NET is unaffected
         (RULE = MULTI_SITE_SECONDARY_PF). If NORMALDAYS is not present in the
         sheet, falls back to "largest current PF, tie-break largest GROSS"
         with a one-time warning.

      3. SET PF = ECR (12% rule) — the primary row's REVISED_PF is set to the
         full ECR EE amount; REVISED_BASIC is re-derived so PF stays exactly
         12% of (BASIC+DA); the change is absorbed through
         REVISED_ATTENDANCE_ALLOWANCE, then REVISED_OTHER_DEDUCTION /
         REVISED_GROSS if the allowance is exhausted — REVISED_NET_PAYABLE
         never moves by more than a rounding rupee.

      4. MINIMUM-WAGE FLOOR (CRITICAL rule) — if the resulting REVISED_BASIC
         would fall below the statutory per-day minimum-wage floor
         (BASIC / NORMALDAYS * ADJ_WORKING_DAYS, using the row's ORIGINAL
         values), the floor wins: BASIC is lifted back to the floor and PF is
         recomputed at 12% of the lifted (BASIC+DA) — even if that means PF no
         longer exactly equals the ECR figure for that row (flagged
         MW_FLOOR_APPLIED). Skipped with a warning if BASIC/NORMALDAYS/
         ADJ_WORKING_DAYS are not present in the sheet.

      5. STATUTORY CEILING CAPS (Rule M2, mandatory / zero violations allowed)
         — REVISED_PF is capped at Rs.1,800 and REVISED_BASIC+DA at Rs.15,000;
         any surplus moves to REVISED_OTHER_DEDUCTION / REVISED_ATTENDANCE_
         ALLOWANCE respectively, NET held throughout (flagged PF_CEILING_CAP).

      6. VALIDATE — every changed row is re-checked against the skill's
         hard-rule set (C1 deductions >=0, C2 NET drift <=Re.1, C3 PF = 12% of
         BASIC+DA, C5 attendance allowance >=0, C6 total deductions >=0,
         C7 GROSS = BASIC+DA+attendance allowance, CAP1 PF<=1800, CAP5
         BASIC+DA<=15000). Any failure is written to the violations report —
         nothing is silently accepted.

    Originals are never modified: corrected copies are written to -OutFolder
    together with per-month change logs, a violations report, an exceptions
    file (rows that needed a non-default route) and a reconciliation summary.

.EXAMPLE
    .\Fix-RevisedPF-M13.ps1 `
        -SalaryFolder 'D:\SALARY\CORRECTED SALARY 25-26 (M13 FINAL)\ESI_WASHING_REALLOCATED' `
        -EcrRoot     'D:\SALARY\ECR PF  2025-26'

.NOTES
    Requires the ImportExcel module (auto-installed from PSGallery on first run).
    Desktop Excel is NOT required. Works on Windows PowerShell 5.1 and PowerShell 7+.
    Scope: PF only. ESI is handled by the separate ESI_Reallocation pipeline and
    is not touched here. Day-projection passes (M3/M4/M5 in the skill) belong to
    the original full-file build and are intentionally out of scope for this
    targeted correction pass.
#>
[CmdletBinding()]
param(
    # Folder containing April_M13_FINAL.xlsx .. March_M13_FINAL.xlsx
    [Parameter(Mandatory)][string]$SalaryFolder,

    # Root of the ECR challan tree (contains APRIL-25, MAY-25, ... MAR-26)
    [Parameter(Mandatory)][string]$EcrRoot,

    # Where corrected files + logs are written. Default: sibling folder next to -SalaryFolder
    [string]$OutFolder,

    # Process only these months (salary-file names), e.g. -Months April,May
    [string[]]$Months,

    # Compute and log everything but do not write the corrected .xlsx files
    [switch]$DryRun,

    # Skip the warn-only comparison against the FY25-26 ECR summary totals
    [switch]$SkipExpectedCheck
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

# ---------------------------------------------------------------- constants --
$PF_RATE      = 0.12
$PF_CEILING   = 1800.0    # Rule M2 CAP 1 — statutory max EE PF per month
$BD_CEILING   = 15000.0   # Rule M2 CAP 5 — statutory max PF-wage base per month

# salary file prefix -> ECR month folder, label, expected (employees, total EE)
# expected values come from ECR_PF_Monthly_Summary_FY2025-26.xlsx (warn-only check)
$MONTH_MAP = @(
    @{ File='April';     Ecr='APRIL-25'; Label='Apr-25'; ExpEmp=16873; ExpEE=23254159 }
    @{ File='May';       Ecr='MAY-25';   Label='May-25'; ExpEmp=16878; ExpEE=23252559 }
    @{ File='June';      Ecr='JUNE-25';  Label='Jun-25'; ExpEmp=17004; ExpEE=23595234 }
    @{ File='July';      Ecr='JULY-25';  Label='Jul-25'; ExpEmp=17158; ExpEE=24272551 }
    @{ File='August';    Ecr='AUG-25';   Label='Aug-25'; ExpEmp=17026; ExpEE=24155548 }
    @{ File='September'; Ecr='SEP-25';   Label='Sep-25'; ExpEmp=17338; ExpEE=24717138 }
    @{ File='October';   Ecr='OCT-25';   Label='Oct-25'; ExpEmp=17114; ExpEE=24620611 }
    @{ File='November';  Ecr='NOV-25';   Label='Nov-25'; ExpEmp=17262; ExpEE=24194136 }
    @{ File='December';  Ecr='DEC-25';   Label='Dec-25'; ExpEmp=17716; ExpEE=25481314 }
    @{ File='January';   Ecr='JAN-26';   Label='Jan-26'; ExpEmp=18040; ExpEE=25984581 }
    @{ File='February';  Ecr='FEB-26';   Label='Feb-26'; ExpEmp=18061; ExpEE=25857826 }
    @{ File='March';     Ecr='MAR-26';   Label='Mar-26'; ExpEmp=18389; ExpEE=26184799 }
)

# required columns — exact header names as they appear in row 1 (first alias found wins)
$COLS = @{
    Uan   = @('UAN NO','UAN','UAN_NO')
    EcrPf = @('ECR_PF')
    Pf    = @('REVISED_PF')
    Basic = @('REVISED_BASIC')
    Da    = @('REVISED_DA')
    Att   = @('REVISED_ATTENDANCE_ALLOWANCE','REVISED_ATTENDANCE_ALLOW','REVISED_ATT_ALW')
    Gross = @('REVISED_GROSS')
    Od    = @('REVISED_OTHER_DEDUCTION','REVISED_OTHER_DED')
    Td    = @('REVISED_TOTAL_DED','REVISED_TOTAL_DEDUCTION')
    Net   = @('REVISED_NET_PAYABLE')
    Emp   = @('EMPCODE')
    Name  = @('FULLNAME')
}
# optional columns — enable Rule M1 (multi-site primary) and the min-wage floor
# when present; each feature degrades gracefully (with a warning) if missing
$OPT_COLS = @{
    NormalDays = @('NORMALDAYS')
    RawBasic   = @('BASIC')
    AdjDays    = @('ADJ_WORKING_DAYS','ADJ_DAYS')
    OrigNet    = @('NETPAYABLE')
}

# ------------------------------------------------------------------ helpers --
function Get-Num {
    param($v)
    if ($null -eq $v) { return 0.0 }
    if ($v -is [double] -or $v -is [int] -or $v -is [long] -or $v -is [decimal]) { return [double]$v }
    $s = ([string]$v).Trim() -replace ',',''
    if ($s -eq '' -or $s -eq '-') { return 0.0 }
    $out = 0.0
    if ([double]::TryParse($s, [System.Globalization.NumberStyles]::Any,
            [System.Globalization.CultureInfo]::InvariantCulture, [ref]$out)) { return $out }
    return 0.0
}

function Get-Uan {
    param($v)
    if ($null -eq $v) { return $null }
    if ($v -is [double] -or $v -is [int] -or $v -is [long] -or $v -is [decimal]) {
        $n = [math]::Round([double]$v)
        if ($n -le 0) { return $null }
        return ([long]$n).ToString([System.Globalization.CultureInfo]::InvariantCulture)
    }
    $s = ([string]$v) -replace '[^0-9]',''
    $s = $s.TrimStart('0')
    if ($s.Length -lt 4) { return $null }   # blank / junk / all zeros
    return $s
}

function RoundR {  # money rounding, .5 away from zero
    param([double]$x, [int]$d = 0)
    return [math]::Round($x, $d, [System.MidpointRounding]::AwayFromZero)
}

# ------------------------------------------------------- ECR challan parsing --
function Read-EcrMonth {
    param([string]$Dir)
    $ee    = @{}   # uan -> summed EE share
    $files = @(Get-ChildItem -LiteralPath $Dir -Recurse -Filter '*.txt' -File | Sort-Object FullName)
    $lines = 0; $bad = 0
    foreach ($f in $files) {
        foreach ($line in [System.IO.File]::ReadAllLines($f.FullName)) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $p = $line -split '#~#'
            if ($p.Count -lt 7) { $bad++; continue }
            $uan = ($p[0] -replace '[^0-9]','').TrimStart('0')
            if ($uan.Length -lt 4) { $bad++; continue }
            $ee[$uan] = [double](Get-Num $ee[$uan]) + (Get-Num $p[6])
            $lines++
        }
    }
    [pscustomobject]@{
        EE = $ee; Files = $files.Count; Lines = $lines; BadLines = $bad
        UniqueUans = $ee.Count
        TotalEE = [double](($ee.Values | Measure-Object -Sum).Sum)
    }
}

# ---------------------------------------------- core primitive: NET-holding --
# Sets REVISED_BASIC and REVISED_PF to the given targets in one atomic move,
# absorbing both deltas through attendance allowance / other deduction / gross
# so REVISED_NET_PAYABLE does not move. Used for the ECR-target set, the
# min-wage floor lift and the statutory ceiling cap alike — they are all the
# same "move to this (basic, pf) pair, hold NET" operation.
function Set-RowBasicPf {
    param($Ws, [int]$Row, $C, [double]$NewBasic, [double]$NewPf, [string]$NoteTag)

    $oldPf    = Get-Num $Ws.Cells[$Row, $C.Pf].Value
    $oldBasic = Get-Num $Ws.Cells[$Row, $C.Basic].Value
    $oldAtt   = Get-Num $Ws.Cells[$Row, $C.Att].Value
    $oldGross = Get-Num $Ws.Cells[$Row, $C.Gross].Value
    $oldOd    = Get-Num $Ws.Cells[$Row, $C.Od].Value
    $oldTd    = Get-Num $Ws.Cells[$Row, $C.Td].Value

    $note = @()
    if ($NoteTag) { $note += $NoteTag }
    $dPf    = $NewPf - $oldPf
    $dBasic = $NewBasic - $oldBasic

    # attendance allowance absorbs the basic move; overflow raises GROSS (OD route)
    $newAtt = $oldAtt - $dBasic
    $dGross = 0.0
    if ($newAtt -lt -0.005) { $dGross = -$newAtt; $newAtt = 0.0; $note += 'GROSS_RAISED_ATT_EXHAUSTED' }

    # hold NET: total deductions must move exactly with GROSS
    $newOd = $oldOd + $dGross - $dPf
    if ($newOd -lt -0.005) {
        $extra   = ($dPf - $oldOd) - $dGross    # extra GROSS needed so OD lands on 0
        $newAtt += $extra
        $dGross += $extra
        $newOd   = 0.0
        $note   += 'ATT_LIFTED_DED_FLOOR'
    }
    $newGross = $oldGross + $dGross
    $newTd    = $oldTd + $dPf + ($newOd - $oldOd)
    $netDrift = ($newGross - $newTd) - ($oldGross - $oldTd)

    $Ws.Cells[$Row, $C.Pf].Value    = RoundR $NewPf 2
    $Ws.Cells[$Row, $C.EcrPf].Value = RoundR $NewPf 2
    $Ws.Cells[$Row, $C.Basic].Value = RoundR $NewBasic 2
    $Ws.Cells[$Row, $C.Att].Value   = RoundR $newAtt 2
    $Ws.Cells[$Row, $C.Gross].Value = RoundR $newGross 2
    $Ws.Cells[$Row, $C.Od].Value    = RoundR $newOd 2
    $Ws.Cells[$Row, $C.Td].Value    = RoundR $newTd 2

    [pscustomobject]@{
        Row = $Row
        Old_REVISED_PF = $oldPf;    New_REVISED_PF = RoundR $NewPf 2;  PF_Delta = RoundR $dPf 2
        Old_Basic = $oldBasic;      New_Basic = RoundR $NewBasic 2
        Old_AttAlw = $oldAtt;       New_AttAlw = RoundR $newAtt 2
        Old_Gross = $oldGross;      New_Gross = RoundR $newGross 2
        Old_OtherDed = $oldOd;      New_OtherDed = RoundR $newOd 2
        Old_TotalDed = $oldTd;      New_TotalDed = RoundR $newTd 2
        Net_Drift = RoundR $netDrift 2
        Note = ($note -join '; ')
    }
}

# Sets REVISED_PF to a target and re-derives REVISED_BASIC so PF stays exactly
# 12% of (BASIC+DA) — the sheet's own M13 rule. PF=0 keeps the existing basic.
function Set-RowPf {
    param($Ws, [int]$Row, $C, [double]$NewPf)
    $da = Get-Num $Ws.Cells[$Row, $C.Da].Value
    $noteTag = $null
    if ($NewPf -gt 0) {
        $newBasic = (RoundR ($NewPf / $PF_RATE)) - $da
        if ($newBasic -lt 0) { $newBasic = 0; $noteTag = 'BASIC_CLAMPED_DA_EXCEEDS_PF_BASE' }
    } else {
        $newBasic = Get-Num $Ws.Cells[$Row, $C.Basic].Value
    }
    return Set-RowBasicPf -Ws $Ws -Row $Row -C $C -NewBasic $newBasic -NewPf $NewPf -NoteTag $noteTag
}

# ------------------------------------------------ Rule M1: multi-site primary --
# Primary = row with the most NORMALDAYS (where the employee genuinely worked
# the most that month); falls back to "largest current PF" if NORMALDAYS is
# unavailable. Ties keep the first row encountered.
function Get-PrimaryRow {
    param($Ws, $Rows, $C, [bool]$UseM1)
    if ($UseM1) {
        $primary = $Rows[0]
        $bestDays = Get-Num $Ws.Cells[$primary, $C.NormalDays].Value
        foreach ($r in $Rows) {
            $d = Get-Num $Ws.Cells[$r, $C.NormalDays].Value
            if ($d -gt $bestDays) { $primary = $r; $bestDays = $d }
        }
        return $primary
    }
    $primary = $Rows[0]
    $bestPf = Get-Num $Ws.Cells[$primary, $C.Pf].Value
    foreach ($r in $Rows) {
        $pf = Get-Num $Ws.Cells[$r, $C.Pf].Value
        if ($pf -gt $bestPf) { $primary = $r; $bestPf = $pf }
        elseif ($pf -eq $bestPf -and
                (Get-Num $Ws.Cells[$r, $C.Gross].Value) -gt (Get-Num $Ws.Cells[$primary, $C.Gross].Value)) { $primary = $r }
    }
    return $primary
}

# ------------------------------------------- CRITICAL rule: minimum-wage floor --
# Returns $null if the floor cannot be evaluated (missing columns) or is not
# breached; otherwise applies the lift and returns the change entry.
function Test-ApplyMinWageFloor {
    param($Ws, [int]$Row, $C, [bool]$Available)
    if (-not $Available) { return $null }
    $rawBasic = Get-Num $Ws.Cells[$Row, $C.RawBasic].Value
    $normDays = Get-Num $Ws.Cells[$Row, $C.NormalDays].Value
    $adjDays  = Get-Num $Ws.Cells[$Row, $C.AdjDays].Value
    if ($normDays -le 0 -or $adjDays -le 0) { return $null }   # nothing to compute against

    $dailyRate = $rawBasic / $normDays
    $floor     = $dailyRate * $adjDays
    $curBasic  = Get-Num $Ws.Cells[$Row, $C.Basic].Value
    if ($curBasic -ge ($floor - 0.5)) { return $null }         # already at/above floor

    $da     = Get-Num $Ws.Cells[$Row, $C.Da].Value
    $newPf  = RoundR (0.12 * ($floor + $da)) 2                  # min-wage wins; 12% recomputes
    return Set-RowBasicPf -Ws $Ws -Row $Row -C $C -NewBasic $floor -NewPf $newPf -NoteTag 'MW_FLOOR_APPLIED'
}

# --------------------------------------------- Rule M2: statutory ceiling caps --
# Mandatory, zero-violations-allowed: PF <= Rs.1,800 and (BASIC+DA) <= Rs.15,000.
function Test-ApplyStatutoryCap {
    param($Ws, [int]$Row, $C)
    $pf = Get-Num $Ws.Cells[$Row, $C.Pf].Value
    if ($pf -le ($PF_CEILING + 0.5)) { return $null }
    $da = Get-Num $Ws.Cells[$Row, $C.Da].Value
    $newBasic = $BD_CEILING - $da
    return Set-RowBasicPf -Ws $Ws -Row $Row -C $C -NewBasic $newBasic -NewPf $PF_CEILING -NoteTag 'PF_CEILING_CAP'
}

# ----------------------------------------- final safety net: BASIC must be >= 0 --
# Genuine edge case (documented in the skill and in the M13 build's own exception
# list): DA alone can exceed the PF base implied by a target PF, and chaining the
# min-wage floor against the statutory cap can otherwise drive BASIC negative.
# BASIC is never written negative — PF is intentionally left as-is (not
# recomputed at 12%) so the row surfaces as a genuine, honestly-flagged
# C3 violation for manual review rather than silently producing a wrong number.
function Test-ApplyBasicFloorZero {
    param($Ws, [int]$Row, $C)
    $basic = Get-Num $Ws.Cells[$Row, $C.Basic].Value
    if ($basic -ge -0.005) { return $null }
    $pf = Get-Num $Ws.Cells[$Row, $C.Pf].Value
    return Set-RowBasicPf -Ws $Ws -Row $Row -C $C -NewBasic 0.0 -NewPf $pf -NoteTag 'BASIC_FLOOR_ZERO_FINAL_MANUAL_REVIEW'
}

# ---------------------------------------------------- change-log record builder --
function New-ChangeRecord {
    param($Ws, $C, [string]$Label, [string]$Uan, [double]$Target, $Entry, [string]$Action)
    $rec = [pscustomobject]([ordered]@{
        Month = $Label; UAN = $Uan
        EMPCODE  = [string]$Ws.Cells[$Entry.Row, $C.Emp].Value
        FULLNAME = [string]$Ws.Cells[$Entry.Row, $C.Name].Value
        Target_ECR_EE = $Target
        Action = $Action
    })
    $Entry.PSObject.Properties | ForEach-Object { $rec | Add-Member -NotePropertyName $_.Name -NotePropertyValue $_.Value }
    return $rec
}

# ------------------------------------------------------------ hard-rule checks --
# C1 OD>=0 . C2 |NET drift|<=1 . C3 |PF-12%(B+D)|<=1 on PF>0 . C5 ATT>=0 .
# C6 TOTAL_DED>=0 . C7 |GROSS-(B+D+ATT)|<=1 . CAP1 PF<=1800 . CAP5 PF>0 -> B+D<=15000
function Test-RowChecks {
    param($Ws, [int]$Row, $C, [double]$OrigNet)
    $pf    = Get-Num $Ws.Cells[$Row, $C.Pf].Value
    $basic = Get-Num $Ws.Cells[$Row, $C.Basic].Value
    $da    = Get-Num $Ws.Cells[$Row, $C.Da].Value
    $att   = Get-Num $Ws.Cells[$Row, $C.Att].Value
    $gross = Get-Num $Ws.Cells[$Row, $C.Gross].Value
    $od    = Get-Num $Ws.Cells[$Row, $C.Od].Value
    $td    = Get-Num $Ws.Cells[$Row, $C.Td].Value
    $net   = Get-Num $Ws.Cells[$Row, $C.Net].Value

    $fails = New-Object System.Collections.Generic.List[string]
    if ($od -lt -0.5) { $fails.Add('C1_OTHER_DED_NEGATIVE') }
    if (($OrigNet -ne $null) -and ([math]::Abs($net - $OrigNet) -gt 1.0)) { $fails.Add('C2_NET_DRIFT') }
    if ($pf -gt 0.5 -and [math]::Abs($pf - (RoundR (0.12 * ($basic + $da)) 2)) -gt 1.0) { $fails.Add('C3_PF_NOT_12PCT') }
    if ($att -lt -0.5) { $fails.Add('C5_ATT_NEGATIVE') }
    if ($td -lt -0.5) { $fails.Add('C6_TOTAL_DED_NEGATIVE') }
    if ([math]::Abs($gross - ($basic + $da + $att)) -gt 1.0) { $fails.Add('C7_GROSS_MISMATCH') }
    if ($pf -gt ($PF_CEILING + 0.5)) { $fails.Add('CAP1_PF_OVER_1800') }
    if ($pf -gt 0.5 -and ($basic + $da) -gt ($BD_CEILING + 0.5)) { $fails.Add('CAP5_BD_OVER_15000') }
    return $fails
}

# -------------------------------------------------------------------- setup --
if (-not (Get-Module -ListAvailable -Name ImportExcel)) {
    Write-Host 'ImportExcel module not found - installing from PSGallery (CurrentUser)...'
    Install-Module ImportExcel -Scope CurrentUser -Force
}
Import-Module ImportExcel

if (-not (Test-Path -LiteralPath $SalaryFolder)) { throw "SalaryFolder not found: $SalaryFolder" }
if (-not (Test-Path -LiteralPath $EcrRoot))      { throw "EcrRoot not found: $EcrRoot" }

if (-not $OutFolder) {
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $OutFolder = Join-Path (Split-Path -Parent (Resolve-Path -LiteralPath $SalaryFolder)) "PF_BOOKS_ALIGNED_$stamp"
}
$logDir = Join-Path $OutFolder '_change_logs'
New-Item -ItemType Directory -Force -Path $OutFolder, $logDir | Out-Null

$todo = $MONTH_MAP
if ($Months) {
    $Months = @($Months | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    $todo = @($MONTH_MAP | Where-Object { $Months -contains $_.File })
}
if (-not $todo) { throw "No months matched -Months $($Months -join ',')" }

$summary       = New-Object System.Collections.Generic.List[object]
$allExceptions = New-Object System.Collections.Generic.List[object]
$allViolations = New-Object System.Collections.Generic.List[object]

# ------------------------------------------------------------------ process --
foreach ($m in $todo) {
    $label      = $m.Label
    $salaryFile = Join-Path $SalaryFolder "$($m.File)_M13_FINAL.xlsx"
    $ecrDir     = Join-Path $EcrRoot $m.Ecr
    Write-Host ''
    Write-Host "=== $label ($($m.File)) ===" -ForegroundColor Cyan

    if (-not (Test-Path -LiteralPath $salaryFile)) { Write-Warning "missing $salaryFile - skipped"; continue }
    if (-not (Test-Path -LiteralPath $ecrDir))     { Write-Warning "missing $ecrDir - skipped";     continue }

    # -- books side
    $ecr = Read-EcrMonth -Dir $ecrDir
    Write-Host ("  ECR : {0} files, {1} lines, {2} UANs, EE total {3:N0}" -f $ecr.Files, $ecr.Lines, $ecr.UniqueUans, $ecr.TotalEE)
    if ($ecr.BadLines) { Write-Warning "  $($ecr.BadLines) unparseable ECR lines skipped" }
    if (-not $SkipExpectedCheck) {
        if ([math]::Abs($ecr.TotalEE - $m.ExpEE) -gt 0.5 -or $ecr.UniqueUans -ne $m.ExpEmp) {
            Write-Warning ("  ECR totals differ from the FY25-26 summary sheet (expected {0:N0} EE / {1} employees). Check for duplicate/extra .txt files in {2}" -f $m.ExpEE, $m.ExpEmp, $ecrDir)
        }
    }

    # -- salary side
    $pkg = New-Object OfficeOpenXml.ExcelPackage (New-Object System.IO.FileInfo $salaryFile)
    try {
        # first worksheet by enumeration (EPPlus indexer is 0-based on .NET Core, 1-based on .NET Framework)
        $ws = @($pkg.Workbook.Worksheets)[0]
        if (-not $ws -or -not $ws.Dimension) { throw "no data in first worksheet of $salaryFile" }
        $lastRow = $ws.Dimension.End.Row
        $lastCol = $ws.Dimension.End.Column

        # header map (exact, case-sensitive, first occurrence wins)
        $hdr = New-Object 'System.Collections.Generic.Dictionary[string,int]' ([System.StringComparer]::Ordinal)
        for ($c = 1; $c -le $lastCol; $c++) {
            $h = $ws.Cells[1, $c].Value
            if ($null -ne $h) {
                $h = ([string]$h).Trim()
                if ($h -ne '' -and -not $hdr.ContainsKey($h)) { $hdr[$h] = $c }
            }
        }
        $C = @{}
        foreach ($key in $COLS.Keys) {
            $col = 0
            foreach ($alias in $COLS[$key]) { if ($hdr.ContainsKey($alias)) { $col = $hdr[$alias]; break } }
            if (-not $col) { throw "column '$($COLS[$key] -join ''' / ''')' not found in $salaryFile. Headers present: $($hdr.Keys -join ' | ')" }
            $C[$key] = $col
        }
        foreach ($key in $OPT_COLS.Keys) {
            $col = 0
            foreach ($alias in $OPT_COLS[$key]) { if ($hdr.ContainsKey($alias)) { $col = $hdr[$alias]; break } }
            $C[$key] = $col   # 0 = not present; callers check for this
        }
        $useM1     = [bool]$C.NormalDays
        $hasMwFloor = [bool]($C.RawBasic -and $C.NormalDays -and $C.AdjDays)
        $hasOrigNet = [bool]$C.OrigNet
        if (-not $useM1)     { Write-Warning '  NORMALDAYS column not found - multi-site primary falls back to "largest current PF" (Rule M1 not applied).' }
        if (-not $hasMwFloor) { Write-Warning '  BASIC/NORMALDAYS/ADJ_WORKING_DAYS not all present - minimum-wage floor pass skipped for this month.' }

        # group data rows by UAN
        $groups = New-Object 'System.Collections.Generic.Dictionary[string,System.Collections.Generic.List[int]]'
        $noUan  = 0
        for ($r = 2; $r -le $lastRow; $r++) {
            $uan = Get-Uan $ws.Cells[$r, $C.Uan].Value
            if (-not $uan) { $noUan++; continue }
            if (-not $groups.ContainsKey($uan)) { $groups[$uan] = New-Object System.Collections.Generic.List[int] }
            $groups[$uan].Add($r)
        }
        Write-Host ("  Sheet: {0} data rows, {1} UANs ({2} rows without UAN)" -f ($lastRow - 1), $groups.Count, $noUan)

        # -- align
        $changeLog     = New-Object System.Collections.Generic.List[object]
        $matchedUans   = 0; $alreadyOk = 0; $changedUans = 0
        $matchedEE     = 0.0; $pfBefore = 0.0; $pfAfter = 0.0

        foreach ($kv in $groups.GetEnumerator()) {
            $uan = $kv.Key
            if (-not $ecr.EE.ContainsKey($uan)) { continue }
            $rows   = $kv.Value
            $target = RoundR ([double]$ecr.EE[$uan]) 2
            $matchedUans++; $matchedEE += $target

            $curSum = 0.0
            foreach ($r in $rows) { $curSum += Get-Num $ws.Cells[$r, $C.Pf].Value }
            $pfBefore += $curSum

            if ([math]::Abs($curSum - $target) -le 0.5) { $alreadyOk++; $pfAfter += $curSum; continue }
            $changedUans++

            # -- Rule M1: pick the primary row and zero out every other row's PF
            $primary = Get-PrimaryRow -Ws $ws -Rows $rows -C $C -UseM1 $useM1
            foreach ($r in $rows) {
                if ($r -eq $primary) { continue }
                $rPf = Get-Num $ws.Cells[$r, $C.Pf].Value
                if ([math]::Abs($rPf) -le 0.005) { continue }   # already zero, nothing to park
                $entry = Set-RowPf -Ws $ws -Row $r -C $C -NewPf 0.0
                $rec = New-ChangeRecord -Ws $ws -C $C -Label $label -Uan $uan -Target $target -Entry $entry -Action 'MULTI_SITE_SECONDARY_PF'
                $changeLog.Add($rec)
                if ($entry.Note) { $allExceptions.Add($rec) }
                if ([math]::Abs($entry.Net_Drift) -gt 0.01) { Write-Warning "  NET drift $($entry.Net_Drift) at row $r (UAN $uan)" }
            }

            # -- set PF = ECR on the primary row (M13 12% rule)
            $entry = Set-RowPf -Ws $ws -Row $primary -C $C -NewPf $target
            $rec = New-ChangeRecord -Ws $ws -C $C -Label $label -Uan $uan -Target $target -Entry $entry -Action 'PRIMARY'
            $changeLog.Add($rec)
            if ($entry.Note) { $allExceptions.Add($rec) }
            if ([math]::Abs($entry.Net_Drift) -gt 0.01) { Write-Warning "  NET drift $($entry.Net_Drift) at row $primary (UAN $uan)" }

            # -- minimum-wage floor (may recompute PF away from the exact ECR figure)
            $mw = Test-ApplyMinWageFloor -Ws $ws -Row $primary -C $C -Available $hasMwFloor
            if ($mw) {
                $rec = New-ChangeRecord -Ws $ws -C $C -Label $label -Uan $uan -Target $target -Entry $mw -Action 'PRIMARY_MW_FLOOR'
                $changeLog.Add($rec); $allExceptions.Add($rec)
            }

            # -- statutory ceiling cap (mandatory, zero violations allowed)
            $cap = Test-ApplyStatutoryCap -Ws $ws -Row $primary -C $C
            if ($cap) {
                $rec = New-ChangeRecord -Ws $ws -C $C -Label $label -Uan $uan -Target $target -Entry $cap -Action 'PRIMARY_CEILING_CAP'
                $changeLog.Add($rec); $allExceptions.Add($rec)
            }

            # -- final safety net: BASIC must never be written negative
            $floorZero = Test-ApplyBasicFloorZero -Ws $ws -Row $primary -C $C
            if ($floorZero) {
                $rec = New-ChangeRecord -Ws $ws -C $C -Label $label -Uan $uan -Target $target -Entry $floorZero -Action 'PRIMARY_BASIC_FLOOR_ZERO'
                $changeLog.Add($rec); $allExceptions.Add($rec)
                Write-Warning "  UAN $uan (row $primary): DA alone exceeds the PF base - BASIC forced to 0, PF left unreconciled to ECR. Manual review required (see PF_M13_Exceptions_Review-style case)."
            }

            $pfAfter += (Get-Num $ws.Cells[$primary, $C.Pf].Value)

            # -- validate every row touched for this UAN
            foreach ($r in $rows) {
                $origNet = if ($hasOrigNet) { Get-Num $ws.Cells[$r, $C.OrigNet].Value } else { $null }
                $fails = Test-RowChecks -Ws $ws -Row $r -C $C -OrigNet $origNet
                foreach ($f in $fails) {
                    $allViolations.Add([pscustomobject]@{
                        Month = $label; UAN = $uan; Row = $r
                        EMPCODE = [string]$ws.Cells[$r, $C.Emp].Value
                        FULLNAME = [string]$ws.Cells[$r, $C.Name].Value
                        Check = $f
                    })
                }
            }
        }

        $diffBefore = RoundR ($matchedEE - $pfBefore) 2
        $diffAfter  = RoundR ($matchedEE - $pfAfter) 2
        Write-Host ("  Match: {0} UANs in both | already OK {1} | corrected {2} | rows changed {3}" -f $matchedUans, $alreadyOk, $changedUans, $changeLog.Count)
        Write-Host ("  PF   : books EE {0:N0} | sheet before {1:N0} (diff {2:N0}) | sheet after {3:N0} (diff {4:N0})" -f $matchedEE, $pfBefore, $diffBefore, $pfAfter, $diffAfter) -ForegroundColor $(if ($diffAfter -eq 0) { 'Green' } else { 'Yellow' })
        $monthViolations = @($allViolations | Where-Object { $_.Month -eq $label })
        if ($monthViolations.Count) {
            Write-Warning "  $($monthViolations.Count) hard-rule check failure(s) - see PF_Validation_Report.csv"
        } else {
            Write-Host '  All hard-rule checks (C1,C2,C3,C5,C6,C7,CAP1,CAP5) PASS on touched rows.' -ForegroundColor Green
        }

        # -- write outputs
        if ($changeLog.Count) {
            $changeLog | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $logDir "$($m.File)_changes.csv")
        }
        if (-not $DryRun) {
            $outFile = Join-Path $OutFolder (Split-Path -Leaf $salaryFile)
            $pkg.SaveAs((New-Object System.IO.FileInfo $outFile))
            Write-Host "  Saved: $outFile"
        }

        $summary.Add([pscustomobject]@{
            MONTH = $label
            ECR_EMPLOYEES = $ecr.UniqueUans
            ECR_TOTAL_EE = RoundR $ecr.TotalEE 0
            MATCHED_UANS = $matchedUans
            MATCHED_ECR_EE = RoundR $matchedEE 0
            SHEET_PF_BEFORE = RoundR $pfBefore 0
            DIFF_BEFORE = $diffBefore
            SHEET_PF_AFTER = RoundR $pfAfter 0
            DIFF_AFTER = $diffAfter
            UANS_CORRECTED = $changedUans
            ROWS_CHANGED = $changeLog.Count
            HARD_RULE_VIOLATIONS = $monthViolations.Count
            MW_FLOOR_APPLIED = $useM1 -and $hasMwFloor
        })
    }
    finally { $pkg.Dispose() }
    [System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()
}

# ------------------------------------------------------------------ summary --
Write-Host ''
Write-Host '================= RECONCILIATION SUMMARY =================' -ForegroundColor Cyan
$summary | Format-Table -AutoSize | Out-String -Width 300 | Write-Host

$summary | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $OutFolder 'PF_Books_Alignment_Summary.csv')
if ($allExceptions.Count) {
    $allExceptions | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $OutFolder 'PF_Alignment_Exceptions.csv')
    Write-Warning "$($allExceptions.Count) row(s) needed a non-default route (min-wage floor / ceiling cap / basic clamp) - review PF_Alignment_Exceptions.csv"
}
if ($allViolations.Count) {
    $allViolations | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $OutFolder 'PF_Validation_Report.csv')
    Write-Warning "$($allViolations.Count) hard-rule check failure(s) across all months - review PF_Validation_Report.csv BEFORE uploading."
} else {
    Write-Host 'Validation: every touched row passes all hard-rule checks (C1,C2,C3,C5,C6,C7,CAP1,CAP5).' -ForegroundColor Green
}

# summary as xlsx too
$sumPkg = New-Object OfficeOpenXml.ExcelPackage
$sumWs  = $sumPkg.Workbook.Worksheets.Add('SUMMARY')
$props  = @('MONTH','ECR_EMPLOYEES','ECR_TOTAL_EE','MATCHED_UANS','MATCHED_ECR_EE','SHEET_PF_BEFORE','DIFF_BEFORE','SHEET_PF_AFTER','DIFF_AFTER','UANS_CORRECTED','ROWS_CHANGED','HARD_RULE_VIOLATIONS','MW_FLOOR_APPLIED')
for ($c = 0; $c -lt $props.Count; $c++) {
    $cell = $sumWs.Cells[1, ($c + 1)]
    $cell.Value = $props[$c]
}
for ($r = 0; $r -lt $summary.Count; $r++) {
    for ($c = 0; $c -lt $props.Count; $c++) {
        $cell = $sumWs.Cells[($r + 2), ($c + 1)]
        $cell.Value = $summary[$r].($props[$c])
    }
}
$sumPkg.SaveAs((New-Object System.IO.FileInfo (Join-Path $OutFolder 'PF_Books_Alignment_Summary.xlsx')))
$sumPkg.Dispose()

$bad = @($summary | Where-Object { $_.DIFF_AFTER -ne 0 })
Write-Host ''
if ($bad.Count) {
    Write-Warning "DIFF_AFTER is non-zero for: $(($bad | ForEach-Object MONTH) -join ', ') - usually means the minimum-wage floor or ceiling cap overrode the exact ECR figure on some rows (by design - see PF_Alignment_Exceptions.csv)."
} else {
    Write-Host 'All months reconcile: sheet REVISED_PF now equals books ECR EE for every matched employee.' -ForegroundColor Green
}
if ($DryRun) { Write-Host '(dry run - no corrected .xlsx written)' -ForegroundColor Yellow }
Write-Host "Output folder: $OutFolder"
