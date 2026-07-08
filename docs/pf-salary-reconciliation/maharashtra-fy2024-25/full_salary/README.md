# Corrected FULL salary sheet — LOCAL run (Maharashtra FY2024-25)

`reconcile_full_salary.py` writes the corrected Maharashtra full salary workbook by applying the
pf-salary-reconciliation skill (PF + ESI) to **your actual salary sheet**.

## Why local
The full salary workbook exceeds the 10 MB Google-Drive connector cap, so it can only be processed
on your machine:
- `Salary comb 2024-25.xlsx` — 224 MB
- `EMPLOYEE SALARY DETAILS - APRIL 24 TO MARCH 25 MAHARASHTRA.xlsx` — 19 MB

## Inputs (all three you already have)
| Input | File |
|---|---|
| Salary sheet | `Salary comb 2024-25.xlsx` (or the 19 MB EMPLOYEE SALARY DETAILS xlsx) — one consolidated sheet with a `MONTH` column |
| PF ECR anchor | `Salary_vs_ECR_PF_EE_Maharashtra_2024-25.xlsx` (the comparison workbook, 12 monthly tabs) |
| ESI anchor | `Maharashtra ESIC  Working 24-25 (Dinesh Sir).xlsx` (the filed register) |

## Run
```bash
pip install pandas openpyxl
# edit the CONFIG block at the top of reconcile_full_salary.py to point at the 3 files above
python reconcile_full_salary.py
```

Outputs (in `out_corrected/`):
- `Maharashtra_Salary_CORRECTED_2024-25.xlsx` — every original column **plus**: `REVISED_EPF`,
  `ECR_PF_CAPPED`, `REVISED_BASIC+DA`, `REVISED_ESI`, `REVISED_OTHER_DEDUCTION`, `ADJ_WORKING_DAYS`,
  `RULE_APPLIED`, `12%_OF_REVISED_BASIC`, `DIFF_12pct_vs_REVISED_EPF`, `PF_DIFF_PARKED`,
  `ESI_DIFF_PARKED`, `REVISED_NET`.
- `reconcile_full_salary_checks.txt` — per-month check log.

## What it does (per row, Net Salary unchanged)
- **PF:** `REVISED_EPF = min(ECR PF, ₹1,800)`; `REVISED_BASIC = ROUND(REVISED_EPF/0.12)` (≤ ₹15,000);
  not-in-ECR → PF zeroed. PF difference parked in `REVISED_OTHER_DEDUCTION` (Total Dedns & Net
  unchanged). `ADJ_WORKING_DAYS` set so an ECR-PF row projects Basic+DA ≤ ₹15,000 full-month (M6).
- **ESI:** `REVISED_ESI =` filed ESIC-register contribution (the deposited anchor); difference
  parked net-neutral.

## Checks printed
`PF gap` (Revised EPF vs ECR-capped, → 0), `C3` (PF = 12% of Basic+DA, ±₹1), `PF ≤ ₹1,800`,
`Basic+DA ≤ ₹15,000`, `Other Ded < 0` (Cond-2 rows to review), `ESI = 0.75% of ESIC wages`.

## Auto-detection
The script auto-detects the header row and maps columns by name (`Employee Code`, `EPF`, `ESI`,
`Basic`/`Earn Basic`, `Days Paid`, `Total Dedns`, `Total Net Salary`, `PF Wages`, `ESIC Wages`,
`MONTH`, …). If your sheet uses different headers, adjust the `WANT` map near the top. Tested
against the FY2024-25 Maharashtra layout.

## Note on scope vs the repo outputs
The already-published `corrected_monthly/` (PF) and `esi/` (ESI) reconciliations are the
**per-employee** results and are final. This script is the extra step that writes those revisions
**back into the full salary workbook** with all original columns — run it locally when you need the
corrected salary sheet itself.
