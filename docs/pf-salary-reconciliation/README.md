# PF / ESI Salary Reconciliation — FY2025-26 (M13 FINAL)

Checks & balances, consolidated summary, and a live dashboard for the ISPL
(Impressions Services) pan-India PF + ESI salary reconciliation, validated
against the `pf-salary-reconciliation` skill.

## What this is

The monthly salary book for FY2025-26 was reconciled so that, per the skill's
**Golden Rules**:

1. `Σ REVISED_PF = ECR_PF` (salary PF matches the EPFO-filed ECR), and
2. `Σ REVISED_ESIC = Future-sheet ESIC`, while
3. **Net Payable never changes** (all differences absorbed via OTHER DEDUCTION /
   attendance allowance).

**M13** is the 13th-month annual true-up (Rule M13: PF = 12% on BASIC+DA),
applied across all 12 months. This folder verifies those outputs and presents
them.

## Files

| File | What it is |
|---|---|
| `dashboard.html` | **Live, self-contained dashboard** — open in any browser, no network needed. KPIs, checks, interactive month-wise trend, PF bridge, M13 rule mix, full tables. |
| `CHECKS_AND_BALANCES_FY2025-26.md` | The full checks & balances report (golden rules, foot-checks, cross-source reconciliation, bridges, M13 stats). |
| `SUMMARY_FY2025-26.csv` | Consolidated month-wise summary + reconciliation anchors. Import into Excel/Sheets. |
| `M13_RULE_STATS_FY2025-26.csv` | Per-month M13 rule-application counts. |
| `reconciliation_data.json` | Machine-readable data powering the dashboard. |
| `build.py` | Reproducible builder — regenerates every artifact above. |

## Result

**7 PASS · 5 REVIEW · 0 FAIL** (14 checks). All golden-rule invariants hold
(NET unchanged, Σ PF = ECR, Σ ESI = Future) and every month foots to the rupee.
The REVIEW items are cross-build / cross-source reconciliation notes, not errors
in the reconciled book — the most material being:

- **October Net** in the `M13_SUMMARY` build is ₹976,861 short of the
  authoritative pivot/monthly figure (pre-final October build) → use the pivot.
- **June PF** in `M13_SUMMARY` is ₹858 short of the ECR anchor → use the pivot/ECR.
- **Jan/Feb gross ≈ 2× run** — possible double/bonus run in those source files;
  Net still ties, but verify before statutory use.

## PF bridge (the key reconciliation)

```
Reconciled PAN PF (= ECR filed)   ₹29,06,52,769   ← golden-rule anchor
+ Back-office PF                   ₹ 1,64,19,591
= Booked PF (salary sheets)       ₹30,70,72,360
Tally EPF-Employee payable        ₹29,67,46,845
```

## Scope & method note

Source of truth is the already-built monthly reconciliation in Google Drive
(folder *ANNUAL SALARY SUMMARY SHEET 25-26* / *CORRECTED SALARY 25-26 (M13
FINAL)*). The per-row monthly files are 18–20 MB each — above the 10 MB Drive
download cap available in this environment — so verification is performed at the
**month-aggregate level** and against the **per-row invariants already asserted
in the M13 FINAL report**. Source workbooks used:

- `Monthly_Salary_Summary_FY2025-26.xlsx` (clean, self-footing month-wise)
- `Salary_Pivot_M13_MONTHWISE.xlsx` (ESI = as-per-Future basis)
- `M13_SUMMARY_and_MERGED_CLBONUS.xlsx` (M13 + CL/Bonus merged)
- `Salary_as_per_Max_SA_consolidated_SUMMARY.xlsx` (Tally books ledger)
- `FINAL_REPORT.md` (rule-application stats + invariants)

To regenerate: `python3 build.py`.
