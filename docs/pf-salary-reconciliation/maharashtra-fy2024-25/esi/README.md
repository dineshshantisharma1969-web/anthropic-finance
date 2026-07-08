# Maharashtra (AISSS) — ESI Reconciliation · FY2024-25

Follow-up to the PF reconciliation. Validates the **filed ESIC register** (the deposited position)
against ESI statutory rules and the salary population, for Apr-24 → Mar-25.

**Rates FY2024-25:** employee **0.75%**, employer **3.25%**, eligibility ceiling **₹21,000/month**.

## Files

| File | What it is |
|---|---|
| `CHECKS_AND_BALANCES_ESI_Maharashtra_FY2024-25.md` | Full ESI checks report — filed position, statutory checks, coverage gaps, month-wise summary |
| `Maharashtra_ESI_Reconciliation_FY2024-25.xlsx` | Combined workbook: SUMMARY + CHECKS + COVERAGE_GAPS + 12 monthly tabs |
| `ESI_FILED_<MONTH>.csv` | Validated filed ESIC register per month (with 0.75%/3.25% audit columns, ₹21k flag, in-salary flag) |
| `ESI_COVERAGE_GAP_<MONTH>.csv` | Salary employees gross ≤ ₹21,000 **not** in the ESIC register (potential coverage gaps) |
| `ESI_COVERAGE_GAPS_YEAR.csv` · `ESI_SUMMARY_FY2024-25.csv` · `ESI_CHECKS_FY2024-25.csv` | Year gap list, month-wise summary, per-month checks |
| `reconcile_esi.py` | Reproducible builder (inputs: `esic_working.xlsx` = ESIC working file, `cmp.xlsx` = PF comparison workbook) |

## Headline

| | ₹ |
|---|--:|
| ESIC wages | 27,00,69,345 |
| ESI employee (0.75%) | 20,34,384 |
| ESI employer (3.25%) | 87,77,254 |
| **ESI total deposited** | **1,08,11,638** |

- Register: 18,261 employee-months, 2,855 unique employees, **100% Maharashtra** (West-only).
- Statutory: 0.75% / 3.25% hold on every row (2 rounding cases ≤ ₹1.5).
- **Open item: 750 ESI coverage gaps** (salary gross ≤ ₹21k, not filed) + 690 above-₹21k
  (contribution-period continuation — generally legitimate).

## Scope

Reconciles the **filed ESIC position**. The skill's row-level salary-side ESI adjustment passes
(E1–E4) edit the full salary sheet's ESI columns, which live in the >10 MB salary workbook that
exceeds the Drive connector cap — run those locally if in-place salary edits are required.
