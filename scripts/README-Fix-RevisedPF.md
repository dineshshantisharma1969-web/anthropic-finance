# Fix-RevisedPF-M13.ps1 — align REVISED_PF with the PF books (ECR) for FY 2025-26

Makes `REVISED_PF` in every monthly `*_M13_FINAL.xlsx` salary sheet equal the
EE share actually deposited per the EPFO ECR challan text files, employee by
employee (UAN-matched) — fixing the month-wise differences reported in
`ECR_PF_Monthly_Summary_FY2025-26.xlsx` (total ₹5,08,332 across the year).

**v2**: implements the golden rules and mandatory checks from the
`pf-salary-reconciliation` skill (`SKILL.md`, consolidated v4 + M1/M2 patches) —
correct multi-site primary-row selection, the statutory PF/wage ceiling caps,
the minimum-wage floor, and a full hard-rule validation report. Only UANs
whose sheet total differs from the ECR figure by more than ₹1 are touched;
everything else is left byte-for-byte alone.

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

Review `PF_Books_Alignment_Summary.csv`, `PF_Validation_Report.csv` and the
`_change_logs\*.csv`, then run again without `-DryRun`.

Useful switches:

- `-Months April,May` — process a subset (also good if RAM is tight; each
  sheet is ~19k rows × 240 columns).
- `-OutFolder <path>` — output location (default: `PF_BOOKS_ALIGNED_<timestamp>`
  next to the salary folder). **Originals are never modified.**
- `-SkipExpectedCheck` — disables the warn-only comparison of parsed ECR
  totals against the FY25-26 summary numbers.

## The pipeline, per changed UAN

Only runs on UANs whose current sheet PF total differs from the ECR EE amount
by more than ₹1. In order:

1. **Multi-site primary (Rule M1).** If the UAN has more than one row, the
   PRIMARY row is the one with the highest `NORMALDAYS` (most days actually
   worked that month) — not simply whichever row already carries PF. Every
   other row's own PF (if any) is zeroed and parked into *that row's own*
   `REVISED_OTHER_DEDUCTION` (`MULTI_SITE_SECONDARY_PF`), so that row's own
   net pay is unaffected. Falls back to "largest current PF" with a one-time
   warning if `NORMALDAYS` isn't present in the sheet.
2. **Set PF = ECR (12% rule).** The primary row's `REVISED_PF` is set to the
   full ECR EE amount; `REVISED_BASIC` is re-derived so PF stays exactly 12%
   of (BASIC+DA) — the sheet's own M13 rule.
3. **Minimum-wage floor (CRITICAL).** If the resulting `REVISED_BASIC` would
   fall below the statutory per-day floor (`BASIC/NORMALDAYS × ADJ_WORKING_DAYS`,
   using the row's *original* values), the floor wins — basic is lifted back
   and PF is recomputed at 12% of the lifted figure, even if that means PF no
   longer exactly equals the ECR figure for that row (`MW_FLOOR_APPLIED`).
   Skipped with a warning if `BASIC`/`NORMALDAYS`/`ADJ_WORKING_DAYS` aren't all
   present.
4. **Statutory ceiling caps (Rule M2, mandatory).** `REVISED_PF` is capped at
   ₹1,800 and `REVISED_BASIC+DA` at ₹15,000; any surplus moves to
   `REVISED_OTHER_DEDUCTION` / `REVISED_ATTENDANCE_ALLOWANCE` (`PF_CEILING_CAP`).
5. **Final safety net.** `REVISED_BASIC` is never written negative — on the
   rare row where DA alone exceeds any workable PF base (a genuine,
   documented edge case — the M13 build's own report lists "2 remaining
   exceptions" of exactly this kind), basic is floored at 0 without
   recomputing PF, and the row is loudly flagged for manual review
   (`BASIC_FLOOR_ZERO_FINAL_MANUAL_REVIEW`) rather than silently producing a
   wrong number.

Every step absorbs its change through `REVISED_ATTENDANCE_ALLOWANCE`, then
`REVISED_OTHER_DEDUCTION` / `REVISED_GROSS` if the allowance is exhausted —
**`REVISED_NET_PAYABLE` never moves**, by construction, at every step.

## Validation (every touched row, every month)

- **C1** deductions ≥ 0 · **C2** NET drift ≤ ₹1 · **C3** PF = 12%×(BASIC+DA) ·
  **C5** attendance allowance ≥ 0 · **C6** total deductions ≥ 0 ·
  **C7** GROSS = BASIC+DA+attendance allowance · **CAP1** PF ≤ ₹1,800 ·
  **CAP5** PF>0 → BASIC+DA ≤ ₹15,000.
- Failures are **not** silently accepted — they're written to
  `PF_Validation_Report.csv` for manual review. In practice this should only
  ever be the rare DA-exceeds-base row from step 5 above.

## Scope

PF only. ESI is handled by the separate ESI_Reallocation pipeline and isn't
touched here. The day-projection passes (M3/M4/M5 in the skill — reducing or
raising `ADJ_WORKING_DAYS` so a row's projected monthly wage clears the PF/ESI
ceilings) belong to the *original* full-file build and are intentionally out
of scope for this targeted correction pass — this script never touches
`ADJ_WORKING_DAYS`.

## Outputs

```
PF_BOOKS_ALIGNED_<timestamp>\
├── April_M13_FINAL.xlsx … March_M13_FINAL.xlsx   (corrected copies)
├── _change_logs\<Month>_changes.csv               (every changed row, old vs new)
├── PF_Alignment_Exceptions.csv                    (rows that needed a non-default route)
├── PF_Validation_Report.csv                       (hard-rule check failures, if any)
├── PF_Books_Alignment_Summary.csv / .xlsx         (per-month reconciliation)
```

After running, re-generate your PowerShell ECR summary against the new folder.
`AMOUNT DIFF (ECR EE − REVISED_PF)` should be ₹0 for every month **except**
where `PF_Alignment_Exceptions.csv` shows a deliberate `MW_FLOOR_APPLIED` or
`BASIC_FLOOR_ZERO_FINAL_MANUAL_REVIEW` override — those are by design, not
bugs. Then replace the files in Drive.

## Known limits

- Columns from later pipelines (`REVISED_GROSS_NEW (final)`, `M8_*`, ESI
  columns) are left untouched; only the PF block and its plug columns move.
- If a month's ECR folder contains duplicate `.txt` exports the EE totals
  double-count — the script warns when parsed totals differ from the FY25-26
  summary figures.
- Rows already reconciling (sum already equals the ECR figure) are left
  completely alone, including their existing multi-site allocation — Rule M1
  is only applied to UANs that actually need a correction.
