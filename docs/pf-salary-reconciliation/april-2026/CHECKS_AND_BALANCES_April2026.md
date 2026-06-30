# PF / ESI Salary Reconciliation — Checks & Balances
## ISPL · APRIL 2026 (FY2026-27)

> **Source:** `April26_Reconciliation_Report.xlsx` (built 2026-06-19 by `reconcile.py` on `April.xlsx` salary sheet + `FORMAT-APRIL_2026_DELHI.xlsx` ECR + `Future reference sheet_2604.xlsx`). The report's Summary rollup is reproduced below; the per-employee PF_Audit tab was re-verified row-by-row in this run.

**Result:** 4 PASS · 1 REVIEW · 0 FAIL. **PF fully reconciled — Σ REVISED_PF = ECR_PF = ₹25,221,042, gap ₹0.**

## Checks

| Check | Status | Detail |
|---|---|---|
| Golden Rule 1 — Σ REVISED_PF = ECR_PF (₹0 gap) | ✅ PASS | Salary PF reconciled to the ECR-filed PF exactly: ₹25,221,042 = ₹25,221,042 (gap ₹0). Holds across 18,389 PF-anchor employees. |
| Row-level PF check — REVISED_PF == ECR_PF on every audited row | ✅ PASS | 17,648/17,648 PF_Audit rows (100.00%) match to the rupee. |
| 12% compliance — REVISED_PF = 12%(REVISED_BASIC+DA) | ✅ PASS | 15,352/15,352 rows with PF>0 (100.00%) land at exactly 12% (REVISED_% = 12 for all). |
| Multi-site secondary rows zeroed (no double-count) | ✅ PASS | 1,754 PF_SECONDARY rows carry PF=0 (parked in OTHER DEDUCTION); PF deposited once per employee at the anchor row. |
| 'Not in ECR' rule applied | ℹ️ INFO | 599+ rows set to BASIC=15001 with PF=0 (employee absent from ECR) — Rule 'Not in ECR' per the skill. |
| ESI vs Future — residual gap = Future-only / secondary-site ESI | ⚠️ REVIEW | Σ REVISED_ESIC ₹321,937 vs Future ₹356,370 → gap ₹34,433. Expected per skill E1 (secondary-site ESI zeroed, deposited at primary; Future-only employees). Full ESI_Audit/Math_Checks tabs of the 20MB report were beyond the fetch limit — confirm ESI totals there before statutory ESI filing. |
| Row reconciliation total | ℹ️ INFO | 21,152 salary rows reconciled = 18,389 PF-anchor + 1,754 PF-secondary + 479 ESI-only + 530 no-PF-no-ESI. |

## Reconciliation by rule group

| Rule group | Rows | Revised PF | ECR PF | Revised ESIC | Future ESI |
|---|--:|--:|--:|--:|--:|
| PF_ANCHOR | 18,389 | 25,221,042 | 25,221,042 | 293,964 | 304,177 |
| PF_SECONDARY | 1,754 | 0 | 0 | 10,213 | 34,400 |
| ESI_ONLY | 479 | 0 | 0 | 17,760 | 17,793 |
| NO_PF_NO_ESI | 530 | 0 | 0 | 0 | 0 |
| **TOTAL** | **21,152** | **25,221,042** | **25,221,042** | **321,937** | **356,370** |

## Row-level PF verification (this run)

- PF_Audit rows checked: **17,648**
- REVISED_PF == ECR_PF exactly: **17,648 (100.00%)**
- Rows with PF>0 at exactly 12%(BASIC+DA): **15,352 (100.00%)**
- Main-PF rows: 15,352 · PF-zero (secondary/not-in-ECR): 2,296 · 'Not in ECR' (BASIC=15001): 599+

## Caveat

The 20 MB report exceeds the 10 MB Drive download cap, and its `ESI_Audit` / `Math_Checks` / `Reconciled_Data` tabs fall beyond the natural-language fetch limit. PF is fully verified; **ESI and gross/net totals should be confirmed in those tabs (or re-run `reconcile.py` locally) before statutory filing.**

*Open `dashboard_April2026.html` for the interactive view.*