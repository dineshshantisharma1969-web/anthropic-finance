# Maharashtra (AISSS) — PF Salary Reconciliation · FY2024-25

Corrected monthly PF sheets for the Maharashtra branch, FY2024-25 (Apr-24 → Mar-25),
produced by applying the `pf-salary-reconciliation` skill to the purpose-built
per-employee salary-vs-ECR comparison workbook.

## What's here

| File | What it is |
|---|---|
| `Maharashtra_PF_Summary_FY2024-25.xlsx` | **Formatted annual Summary sheet** — month-wise table, reconciliation bridge, rule stats, checks status (one page) |
| `CHECKS_AND_BALANCES_Maharashtra_FY2024-25.md` | Full checks report — Golden Rules, statutory caps, integrity checks, month-wise summary, rule stats |
| `Maharashtra_PF_Corrected_Monthly_FY2024-25.xlsx` | Combined workbook: SUMMARY + CHECKS + RULE_STATS + 12 corrected monthly tabs |
| `corrected_monthly/CORRECTED_<MONTH>.csv` | The 12 corrected monthly sheets (one row per employee) |
| `SUMMARY_FY2024-25.csv` · `RULE_STATS_FY2024-25.csv` · `CHECKS_FY2024-25.csv` | Month-wise summary, rule counts, per-month check results |
| `reconcile_mh.py` | Reproducible builder (re-runs all of the above from `cmp.xlsx`) |

## Corrected-sheet columns

Per employee, per month: identity (EMP CODE, NAME, DESIGNATION, EPF/UAN, SITE, BRANCH),
days (`M/DAYS` divisor, `NORMALDAYS`, `NCP`), original state (`ORIG_BASIC(+DA)`, `GROSS`,
`ORIG_PF`), ECR (`ECR_PF filed`, `ECR_PF_CAPPED (min 1800)`, `ABOVE_1800_SURPLUS`, `PF SOURCE`),
and the reconciled result: `RULE_APPLIED`, `REVISED_PF`, `REVISED_BASIC(+DA)`,
`ADJ_WORKING_DAYS`, `PF_DIFF_PARKED_IN_OTHER_DED`, plus the 12% audit columns
(`12% OF REVISED_BASIC`, `DIFF (12% vs REVISED_PF)`), `BD_MONTHLY_PROJECTION`, and `REMARK`.

## Method (PF)

1. **Anchor** — `ECR_PF_CAPPED = min(filed ECR, ₹1,800)` per employee (statutory EE cap).
2. **Rules** — NO_ADJUSTMENT (salary already = ECR), Case A/B (ECR < salary), Cond 2 (ECR > salary),
   Not-in-ECR (PF zeroed, parked), Multi-site secondary (max-NORMALDAYS row is primary; duplicate
   secondaries zeroed and parked).
3. **12% lock-in (v4)** — `REVISED_BASIC = round(REVISED_PF / 0.12)`, PF capped ≤ ₹1,800, basic ≤ ₹15,000.
4. **Day adjustment (M6)** — `ADJ_WORKING_DAYS` set so an ECR-PF row projects BD ≤ ₹15,000 full-month,
   and a not-in-ECR row projects ≥ ₹15,000 (justifying PF absence).
5. **Net-neutral** — every PF change is parked in OTHER DEDUCTION, so Net Payable never moves.

## West-only ECR (per instruction)

The raw challan file is **"Challan Data (West & South)"** and genuinely mixes regions
(Mumbai/Pune/Nagpur/Aurangabad = West/Maharashtra; Bangalore/Hyderabad/Chennai/Vishakhapatnam
= South). The reconciliation uses **West/Maharashtra rows only**. Verified end-to-end for
Apr / Oct / Jan against the raw challan: **0 empcodes appear in both West and South**, and every
matched Maharashtra employee's ECR equals the West-only sum ⇒ **₹0 South leakage**. No figures
change; the pre-built basis was already West-only.

## Data sources (Google Drive — `dinesh@impressionsgroup.in`)

| Item | Drive ID |
|---|---|
| Folder — `MAHARASHTRA ASSSIS DATA 24-25` | `13Q9wUiqy4UMwc-0VWi8EEtF3fDSbC2wc` |
| Basis — `Salary_vs_ECR_PF_EE_Maharashtra_2024-25.xlsx` | `16yIgE9sVtxwM957hX5jExmca5KHOj7M1` |
| ECR — `PF CONSOLIDATED (CHALLAN+DMART+PF_EE) MAHARASHTRA 24-25` (12 monthly files) | `1DF8zGcEhH7gJcIYc5N2_Uyy8ijCCy9zc` |
| Raw challan — `CHALLAN DATA (WEST & SOUTH) 2024-25` | `1nwd3u3RXagBiBAWs4L3sHCKJM0QajBxb` |
| Salary — `EMPLOYEE SALARY DETAILS 24-25 WITH PF` (>10 MB, local run) | `1P7MIqiWKlPcVk4udl_8XBnBgeHcItxSdLmEsqbPeKXw` |
| Salary comb (224 MB, local run) | `1xBpQXiS3K00ePA3Xqg4UlhcdpGRBvqbI` |
| ESIC — `ESIC DATA 24-25 MAHARASHTRA` (for the ESI pass) | `1Dxa4nFpXlAzxE46aQ218zDvXsVt8js3H` |

## Scope

**PF only.** ESI reconciliation against the ESIC "Future" register needs the full salary sheet's
per-employee ESI columns (in the >10 MB salary files that exceed the connector cap) and should be
run locally per the master skill. See §6 of the checks report.

## Re-run

```
python3 reconcile_mh.py     # expects cmp.xlsx (the comparison workbook) alongside; writes corrected sheets + summaries
python3 build_summary.py     # builds the formatted Maharashtra_PF_Summary_FY2024-25.xlsx from the summaries
```
