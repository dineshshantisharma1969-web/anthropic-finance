<#
.SYNOPSIS
    Aligns REVISED_PF in the monthly M13_FINAL salary sheets with the EE share
    actually deposited per the EPFO ECR challan files (books), for FY 2025-26.

.DESCRIPTION
    For every month (April..March):
      1. Parses all ECR text files (UAN#~#NAME#~#GROSS#~#EPF#~#EPS#~#EDLI#~#EE#~#EPS_ER#~#DIFF#~#NCP#~#REFUND)
         under the month's folder inside -EcrRoot and totals the EE share per UAN.
      2. Opens <Month>_M13_FINAL.xlsx from -SalaryFolder and, for every UAN present
         in both the ECR and the sheet, makes the sum of REVISED_PF across that
         UAN's rows equal the ECR EE amount.
    When a row's PF changes the M13 rule is re-applied and NET is held:
      - REVISED_BASIC   = round(PF / 0.12) - REVISED_DA   (clamped at 0, exception logged)
      - REVISED_ATTENDANCE_ALLOWANCE absorbs the basic change so REVISED_GROSS holds;
        if it would go negative, GROSS rises and the rise goes to REVISED_OTHER_DEDUCTION
      - REVISED_OTHER_DEDUCTION takes (dGROSS - dPF) so that
        REVISED_NET_PAYABLE (= GROSS - TOTAL_DED) does not move by a single rupee;
        if it would go negative, the attendance allowance is lifted instead
      - ECR_PF column is set to the same value as REVISED_PF on changed rows
    Multi-site UANs: the row currently carrying the largest REVISED_PF is treated as
    primary and receives the balancing amount; if the target is below the other rows'
    total, the non-primary rows are zeroed first.
    Rows whose UAN is absent from the ECR (back office / not in ECR) are not touched.

    Originals are never modified: corrected copies are written to -OutFolder together
    with per-month change logs, an exceptions file and a reconciliation summary.

.EXAMPLE
    .\Fix-RevisedPF-M13.ps1 `
        -SalaryFolder 'D:\SALARY\CORRECTED SALARY 25-26 (M13 FINAL)\ESI_WASHING_REALLOCATED' `
        -EcrRoot     'D:\SALARY\ECR PF  2025-26'

.NOTES
    Requires the ImportExcel module (auto-installed from PSGallery on first run).
    Desktop Excel is NOT required. Works on Windows PowerShell 5.1 and PowerShell 7+.
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
$PF_RATE = 0.12

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

# exact header names as they appear in row 1 (first alias found wins)
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

# ------------------------------------------- apply new PF to one salary row --
function Set-RowPf {
    param($Ws, [int]$Row, $C, [double]$NewPf)

    $oldPf    = Get-Num $Ws.Cells[$Row, $C.Pf].Value
    $oldBasic = Get-Num $Ws.Cells[$Row, $C.Basic].Value
    $da       = Get-Num $Ws.Cells[$Row, $C.Da].Value
    $oldAtt   = Get-Num $Ws.Cells[$Row, $C.Att].Value
    $oldGross = Get-Num $Ws.Cells[$Row, $C.Gross].Value
    $oldOd    = Get-Num $Ws.Cells[$Row, $C.Od].Value
    $oldTd    = Get-Num $Ws.Cells[$Row, $C.Td].Value

    $note = @()
    $dPf  = $NewPf - $oldPf

    # M13: basic derived from PF so that PF = 12% of (BASIC + DA); PF=0 rows keep basic
    if ($NewPf -gt 0) {
        $newBasic = (RoundR ($NewPf / $PF_RATE)) - $da
        if ($newBasic -lt 0) { $newBasic = 0; $note += 'BASIC_CLAMPED_DA_EXCEEDS_PF_BASE' }
    } else {
        $newBasic = $oldBasic
    }

    # attendance allowance absorbs the basic move; overflow raises GROSS (OD route)
    $dBasic = $newBasic - $oldBasic
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
    $Ws.Cells[$Row, $C.Basic].Value = RoundR $newBasic 2
    $Ws.Cells[$Row, $C.Att].Value   = RoundR $newAtt 2
    $Ws.Cells[$Row, $C.Gross].Value = RoundR $newGross 2
    $Ws.Cells[$Row, $C.Od].Value    = RoundR $newOd 2
    $Ws.Cells[$Row, $C.Td].Value    = RoundR $newTd 2

    [pscustomobject]@{
        Row = $Row
        Old_REVISED_PF = $oldPf;    New_REVISED_PF = RoundR $NewPf 2;  PF_Delta = RoundR $dPf 2
        Old_Basic = $oldBasic;      New_Basic = RoundR $newBasic 2
        Old_AttAlw = $oldAtt;       New_AttAlw = RoundR $newAtt 2
        Old_Gross = $oldGross;      New_Gross = RoundR $newGross 2
        Old_OtherDed = $oldOd;      New_OtherDed = RoundR $newOd 2
        Old_TotalDed = $oldTd;      New_TotalDed = RoundR $newTd 2
        Net_Drift = RoundR $netDrift 2
        Note = ($note -join '; ')
    }
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

            $cur = @{}; $curSum = 0.0
            foreach ($r in $rows) { $cur[$r] = Get-Num $ws.Cells[$r, $C.Pf].Value; $curSum += $cur[$r] }
            $pfBefore += $curSum

            if ([math]::Abs($curSum - $target) -le 0.5) { $alreadyOk++; $pfAfter += $curSum; continue }
            $changedUans++

            # primary row = biggest current PF (tie: biggest REVISED_GROSS, then first)
            $primary = $rows[0]
            foreach ($r in $rows) {
                if ($cur[$r] -gt $cur[$primary]) { $primary = $r }
                elseif ($cur[$r] -eq $cur[$primary] -and
                        (Get-Num $ws.Cells[$r, $C.Gross].Value) -gt (Get-Num $ws.Cells[$primary, $C.Gross].Value)) { $primary = $r }
            }
            $othersSum = $curSum - $cur[$primary]
            $newPrimary = $target - $othersSum
            $zeroOthers = $false
            if ($newPrimary -lt 0) { $zeroOthers = $true; $newPrimary = $target }

            foreach ($r in $rows) {
                $newPf = if ($r -eq $primary) { $newPrimary } elseif ($zeroOthers) { 0.0 } else { $cur[$r] }
                if ([math]::Abs($newPf - $cur[$r]) -le 0.005) { $pfAfter += $cur[$r]; continue }
                $entry = Set-RowPf -Ws $ws -Row $r -C $C -NewPf $newPf
                $pfAfter += $newPf
                $rec = [pscustomobject]([ordered]@{
                    Month = $label; UAN = $uan
                    EMPCODE  = [string]$ws.Cells[$r, $C.Emp].Value
                    FULLNAME = [string]$ws.Cells[$r, $C.Name].Value
                    Target_ECR_EE = $target
                    Action = $(if ($r -eq $primary) { 'PRIMARY' } else { 'SECONDARY_ZEROED' })
                })
                $entry.PSObject.Properties | ForEach-Object { $rec | Add-Member -NotePropertyName $_.Name -NotePropertyValue $_.Value }
                $changeLog.Add($rec)
                if ($entry.Note) { $allExceptions.Add($rec) }
                if ([math]::Abs($entry.Net_Drift) -gt 0.01) { Write-Warning "  NET drift $($entry.Net_Drift) at row $r (UAN $uan)" }
            }
        }

        $diffBefore = RoundR ($matchedEE - $pfBefore) 2
        $diffAfter  = RoundR ($matchedEE - $pfAfter) 2
        Write-Host ("  Match: {0} UANs in both | already OK {1} | corrected {2} | rows changed {3}" -f $matchedUans, $alreadyOk, $changedUans, $changeLog.Count)
        Write-Host ("  PF   : books EE {0:N0} | sheet before {1:N0} (diff {2:N0}) | sheet after {3:N0} (diff {4:N0})" -f $matchedEE, $pfBefore, $diffBefore, $pfAfter, $diffAfter) -ForegroundColor $(if ($diffAfter -eq 0) { 'Green' } else { 'Red' })

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
    Write-Warning "$($allExceptions.Count) row(s) needed special handling - review PF_Alignment_Exceptions.csv"
}

# summary as xlsx too
$sumPkg = New-Object OfficeOpenXml.ExcelPackage
$sumWs  = $sumPkg.Workbook.Worksheets.Add('SUMMARY')
$props  = @('MONTH','ECR_EMPLOYEES','ECR_TOTAL_EE','MATCHED_UANS','MATCHED_ECR_EE','SHEET_PF_BEFORE','DIFF_BEFORE','SHEET_PF_AFTER','DIFF_AFTER','UANS_CORRECTED','ROWS_CHANGED')
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
    Write-Warning "DIFF_AFTER is non-zero for: $(($bad | ForEach-Object MONTH) -join ', ') - investigate before uploading."
} else {
    Write-Host 'All months reconcile: sheet REVISED_PF now equals books ECR EE for every matched employee.' -ForegroundColor Green
}
if ($DryRun) { Write-Host '(dry run - no corrected .xlsx written)' -ForegroundColor Yellow }
Write-Host "Output folder: $OutFolder"
