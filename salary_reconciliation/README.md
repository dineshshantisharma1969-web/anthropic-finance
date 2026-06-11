# Salary reconciliation checks — PF / ESI / gross projection

`check_pf_esi_gross.py` runs three month-by-month sanity checks over the
RECONCILED monthly salary files, following `PF_SALARY_RECONCILIATION_SKILL_v4.md`
and the `build_*_management_review.py` reference pipeline.

## The checks

| Check | Rule | Skill ref |
|---|---|---|
| **1. PF = 12%** | For every row with `REVISED_PF > 0`, `REVISED_PF` must equal `0.12 × (REVISED_BASIC + REVISED_DA)` within ±₹1 | C3 |
| **2. PF ceiling** | Where the **ECR PF** column is populated (`ECR_PF > 0`), `REVISED_BASIC + REVISED_DA` should normally be **< ₹15,000** (PF wage ceiling → max EE PF ₹1,800). Rows above it are listed as **exceptions** (genuine high earners contributing above the ceiling) — not errors. Also reports the full-month Basic+DA projection > ₹15,000 view (M6). | M6 |
| **3. ESI** | (a) For rows with `REVISED_ESIC > 0`, it must equal `0.0075 × REVISED_GROSS` within ±₹1. (b) Where ESI is present, `REVISED_GROSS` should normally be **≤ ₹21,000** (ESI ceiling); rows above are exceptions. | C4 / Rule B |
| **4. Gross too high** | Full-month-equivalent gross = `REVISED_GROSS × days_in_month / ADJ_WORKING_DAYS` (`MONTHLY_GROSS_PROJECTION`). Buckets rows >₹50k and >₹100k and lists the worst offenders. | M7 |

> Note on Check 3a: per the skill, the 0.75% ESI target is **informational** and is
> deliberately *relaxed* on rows where `ESIC AS PER FUTURE` (the filed figure) or NET
> preservation forces a gap. Expect many "mismatches" here that are accepted-by-design,
> not defects — read 3a alongside `ESIC AS PER FUTURE`.

## Usage

```bash
python check_pf_esi_gross.py /path/to/RECONCILED --out salary_checks_report.xlsx
```

The folder should hold the monthly files (`April.xlsx` … `March.xlsx`). Each is read
from its first sheet. Column names are matched tolerantly (`REVISED_BASIC`,
`ECR_PF`/`ECR PF`, `ESIC AS PER FUTURE`/`ESIC_AS_PER_FUTURE`, etc.). The script prints
a per-month summary and a consolidated table, and (with `--out`) writes an Excel
workbook with a Summary sheet plus per-month exception sheets.

## Why this is a local script

The 12 monthly files are 7.7–21 MB each. They cannot be pulled through the Google
Drive connector in full (binary download fails on multi-MB files; the text reader
truncates at ~1,800 rows). Run this where the full `.xlsx` files live (e.g. the
local `V2 SALARY FOLDER 25-26`, or the downloaded RECONCILED folder).
