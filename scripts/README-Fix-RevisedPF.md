# Fix-RevisedPF-M13.ps1 — align REVISED_PF with the PF books (ECR) for FY 2025-26

Makes `REVISED_PF` in every monthly `*_M13_FINAL.xlsx` salary sheet equal the
EE share actually deposited per the EPFO ECR challan text files, employee by
employee (UAN-matched). Fixes the month-wise differences reported in
`ECR_PF_Monthly_Summary_FY2025-26.xlsx` (total ₹5,08,332 across the year).

## What you need on your machine

- Windows PowerShell 5.1 or PowerShell 7 (both work). Desktop Excel is NOT needed.
- Internet on first run only — the script auto-installs the `ImportExcel`
  module from PSGallery if missing.
- Local copies of:
  - the salary folder with `April_M13_FINAL.xlsx` … `March_M13_FINAL.xlsx`
    (Drive: `CORRECTED SALARY 25-26 (M13 FINAL)…\ESI_WASHING_REALLOCATED`)
  - the ECR tree with month folders `APRIL-25` … `MAR-26`
    (Drive: `ECR PF  2025-26`)

## How to run

Dry run first (computes everything, writes logs + summary, touches nothing):

```powershell
.\Fix-RevisedPF-M13.ps1 `
    -SalaryFolder 'D:\SALARY\ESI_WASHING_REALLOCATED' `
    -EcrRoot      'D:\SALARY\ECR PF  2025-26' `
    -DryRun
```

Review `PF_Books_Alignment_Summary.csv` (DIFF_AFTER must be 0 for all months)
and the `_change_logs\*.csv`, then run again without `-DryRun`.

Useful switches:

- `-Months April,May` — process a subset (also good if RAM is tight; each
  sheet is ~19k rows × 240 columns).
- `-OutFolder <path>` — output location (default: `PF_BOOKS_ALIGNED_<timestamp>`
  next to the salary folder). Originals are never modified.
- `-SkipExpectedCheck` — disables the warn-only comparison of parsed ECR
  totals against the FY25-26 summary numbers.

## What it changes per corrected row

For every UAN present in both the ECR and the sheet whose REVISED_PF total
differs from the books EE amount:

| Column | Rule |
|---|---|
| `REVISED_PF`, `ECR_PF` | set to the ECR EE share (books) |
| `REVISED_BASIC` | `round(PF / 0.12) − REVISED_DA` (M13 rule; clamped at 0 if DA alone exceeds the PF base — logged as exception) |
| `REVISED_ATTENDANCE_ALLOWANCE` | absorbs the basic change so `REVISED_GROSS` holds; if exhausted, GROSS rises (logged) |
| `REVISED_OTHER_DEDUCTION` | plug so deductions move exactly with GROSS; floored at 0 via attendance-allowance lift (logged) |
| `REVISED_TOTAL_DED` | recomputed |
| `REVISED_NET_PAYABLE` | **never changes** — net drift is held at zero, row by row |

Multi-site UANs: the row with the largest current PF is primary and takes the
balancing amount; other rows are zeroed only if the target is below their total.
Rows whose UAN is not in the ECR (back office / not in ECR) are untouched.

## Outputs

```
PF_BOOKS_ALIGNED_<timestamp>\
├── April_M13_FINAL.xlsx … March_M13_FINAL.xlsx   (corrected copies)
├── _change_logs\<Month>_changes.csv               (every changed row, old vs new)
├── PF_Alignment_Exceptions.csv                    (rows that needed a special route)
├── PF_Books_Alignment_Summary.csv / .xlsx         (per-month reconciliation)
```

After running, re-generate your PowerShell ECR summary against the new folder —
`AMOUNT DIFF (ECR EE − REVISED_PF)` should be 0 for every month — then replace
the files in Drive.

## Known limits

- Columns from later pipelines (`REVISED_GROSS_NEW (final)`, `M8_*`, ESI
  columns) are left untouched; only the PF block and its plug columns move.
- If a month's ECR folder contains duplicate `.txt` exports the EE totals
  double-count — the script warns when parsed totals differ from the FY25-26
  summary figures.
