# PF Salary Reconciliation — Checks & Balances
## Maharashtra (AISSS) · FY2024-25 (Apr-24 → Mar-25)

> **Scope:** Maharashtra-only PF reconciliation for FY2024-25 — 12 monthly payrolls,
> ~1,750 employees/month (21,551 employee-months). Salary-sheet employee PF is reconciled
> against the EPFO-filed ECR (Electronic Challan cum Return) per the `pf-salary-reconciliation`
> skill (Golden Rules + the four PF rules + statutory caps M2/CAP + M6/day-adjustment +
> post-recon integrity checks). ECR source = **West & South Challan (West/Maharashtra rows only)**
> + **DMART Challan**. Basis file: `Salary_vs_ECR_PF_EE_Maharashtra_2024-25.xlsx`
> (Drive `16yIgE9sVtxwM957hX5jExmca5KHOj7M1`), independently verified against the raw
> `PF CONSOLIDATED` monthly files and the raw `Challan Data (West & South)` sources.

**Result:** all hard checks **0 violations** on every month. Golden Rule 1 holds against the
statutory-capped ECR anchor with **₹0 gap**. 10 at-ceiling daily-wage rows are documented
exceptions (not failures).

---

## 1. Golden Rules (skill invariants)

| Rule | Status | Detail |
|---|---|---|
| **GR1** — Σ REVISED_PF = ECR_PF anchor (per row, ₹0 gap) | ✅ PASS | Anchor = `ECR_PF_CAPPED = min(filed ECR, ₹1,800)`. Σ REVISED_PF = **₹3,02,29,684** = Σ capped anchor. Max per-row gap **₹0.00** on all 12 months. |
| **GR2** — NET PAYABLE never changes | ✅ PASS (by construction) | Every PF adjustment is absorbed into OTHER DEDUCTION (or, for Cond 2, reduces it). PF↓ ⇒ OTHER_DED↑ by the same amount ⇒ Net Payable unchanged. Total PF parked = **₹22,92,983** (net-neutral). |
| **West-only ECR** (per instruction) | ✅ PASS | ECR anchor uses **West/Maharashtra challan rows only**. Verified end-to-end for Apr / Oct / Jan against the raw West & South challan: **0 empcodes appear in both West and South**, and every matched Maharashtra employee's ECR = West-only sum ⇒ **₹0 South leakage**. |

## 2. Statutory & integrity checks (per month — all 0)

| ID | Check | Result |
|---|---|---|
| **C3** | REVISED_PF = 12% × REVISED_BASIC(+DA) on PF>0 rows (±₹1) | **0** violations |
| **CAP1** | REVISED_PF ≤ ₹1,800 | **0** violations |
| **CAP5** | REVISED_BASIC(+DA) ≤ ₹15,000 on PF>0 rows | **0** violations |
| **C10 / M6** | ECR-PF row: BD monthly projection ≤ ₹15,000 | **0** violations |
| **P2** | Not-in-ECR row: full-month BD projection ≥ ₹15,000 (justifies PF absence) | **0** strictly-below |
| **C9** | ADJ_WORKING_DAYS ∈ [1, full-month] | **0** out of range |

**Documented exceptions (not failures):** 10 not-in-ECR rows across the year are daily-wage
earners at exactly ₹500/day × full month = **₹15,000** (the ceiling boundary). They sit *at*
the ceiling, so their PF-absence cannot be pushed strictly above ₹15,000 by day reduction. Flagged
`P2_atCeiling_15000_exceptions`: Jun 4, Jul 1, Oct 1, Dec 1, Feb 2, Mar 1.

## 3. PF reconciliation bridge (year)

| Line | ₹ |
|---|--:|
| Original salary PF (employee EE) | 3,25,22,667.12 |
| ECR PF filed (West + DMART, matched) | 3,06,22,337.68 |
| − Above-₹1,800 statutory cap surplus | (3,57,385.12) |
| − Secondary multi-site duplicate ECR (moved to primary row) | (35,268.56) |
| **= ECR_PF_CAPPED anchor = REVISED_PF** | **3,02,29,684.00** |
| PF parked in OTHER DEDUCTION (net-neutral) | 22,92,983.12 |
| Not-in-ECR employees (PF zeroed, parked) | 1,306 emp-months |

`ECR filed − capped = ₹3,92,653.68 = cap surplus ₹3,57,385.12 + secondary duplicate ECR ₹35,268.56.`

## 4. Consolidated month-wise summary (₹)

| Month | Rows | Orig Salary PF | ECR Filed | ECR Capped = Revised PF | PF Gap | Above-1800 Surplus | PF Parked (OTHER_DED) |
|---|--:|--:|--:|--:|--:|--:|--:|
| Apr-24 | 1,757 | 2,584,328 | 2,402,823 | 2,379,010 | 0 | 23,636 | 205,318 |
| May-24 | 1,713 | 2,534,769 | 2,379,620 | 2,350,266 | 0 | 25,872 | 184,503 |
| Jun-24 | 1,818 | 2,667,492 | 2,513,706 | 2,477,028 | 0 | 26,059 | 190,464 |
| Jul-24 | 1,820 | 2,710,675 | 2,552,090 | 2,522,986 | 0 | 28,756 | 187,690 |
| Aug-24 | 1,820 | 2,802,253 | 2,631,887 | 2,597,426 | 0 | 30,804 | 204,827 |
| Sep-24 | 1,825 | 2,756,166 | 2,589,093 | 2,545,659 | 0 | 32,835 | 210,506 |
| Oct-24 | 1,799 | 2,812,260 | 2,650,968 | 2,614,187 | 0 | 33,583 | 198,073 |
| Nov-24 | 1,811 | 2,630,461 | 2,475,530 | 2,442,236 | 0 | 31,578 | 188,225 |
| Dec-24 | 1,745 | 2,691,269 | 2,547,338 | 2,516,763 | 0 | 29,213 | 174,506 |
| Jan-25 | 1,831 | 2,753,834 | 2,607,369 | 2,576,861 | 0 | 30,398 | 176,973 |
| Feb-25 | 1,820 | 2,798,222 | 2,645,120 | 2,613,353 | 0 | 31,767 | 184,869 |
| Mar-25 | 1,792 | 2,780,938 | 2,626,794 | 2,593,910 | 0 | 32,884 | 187,028 |
| **TOTAL** | **21,551** | **32,522,667** | **30,622,338** | **30,229,684** | **0** | **357,385** | **2,292,983** |

## 5. Rule-application statistics (rows per rule)

| Month | No Adjustment | Not in ECR | Multi-site Secondary | Case A | Case B | Cond 2 |
|---|--:|--:|--:|--:|--:|--:|
| Apr-24 | 1,624 | 130 | 2 | 1 | 0 | 0 |
| May-24 | 1,602 | 107 | 4 | 0 | 0 | 0 |
| Jun-24 | 1,701 | 107 | 9 | 0 | 1 | 0 |
| Jul-24 | 1,702 | 116 | 1 | 0 | 1 | 0 |
| Aug-24 | 1,698 | 112 | 8 | 0 | 2 | 0 |
| Sep-24 | 1,692 | 115 | 9 | 0 | 0 | 9 |
| Oct-24 | 1,691 | 103 | 5 | 0 | 0 | 0 |
| Nov-24 | 1,707 | 102 | 2 | 0 | 0 | 0 |
| Dec-24 | 1,647 | 95 | 2 | 0 | 1 | 0 |
| Jan-25 | 1,725 | 103 | 2 | 0 | 1 | 0 |
| Feb-25 | 1,716 | 104 | 0 | 0 | 0 | 0 |
| Mar-25 | 1,690 | 102 | 0 | 0 | 0 | 0 |

**Read:** the salary sheet already deducted PF at ECR values for the vast majority of matched
employees (`NO_ADJUSTMENT`). The reconciliation's real work is (a) zeroing PF for ~1,306
not-in-ECR employee-months and parking it net-neutrally, (b) applying the ₹1,800 statutory cap
(991 emp-months carried a filed EE above ₹1,800), and (c) day-adjusting rows for PF/ESI ceiling
self-consistency.

## 6. Scope note — ESI

This pass reconciles **PF only**. ESI reconciliation against the ESIC "Future" register requires
the full salary sheet's per-employee ESI columns (ESI wages, ESIC deducted, attendance allowance,
net payable), which live in the 224 MB `Salary comb 2024-25.xlsx` / the `EMPLOYEE SALARY DETAILS
24-25 WITH PF` sheet — both exceed the 10 MB Google-Drive connector download cap and must be run
locally with `reconcile.py` per the master skill. The ESIC source data is indexed in the
knowledgebase (`ESIC DATA 24-25 MAHARASHTRA`, Drive `1Dxa4nFpXlAzxE46aQ218zDvXsVt8js3H`).

---
*Generated by `reconcile_mh.py` from the verified per-employee monthly comparison workbook.
Corrected monthly sheets: `corrected_monthly/CORRECTED_<MONTH>.csv` and the combined
`Maharashtra_PF_Corrected_Monthly_FY2024-25.xlsx`.*
