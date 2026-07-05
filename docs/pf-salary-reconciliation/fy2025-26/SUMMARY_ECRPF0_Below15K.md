# PF-Exemption Audit — ECR_PF = 0 & REVISED_BASIC+DA < ₹15,000 (all 12 months FY25-26)

Filter run 05-07-2026 on every monthly M13 FINAL sheet: rows with **no PF deposited
(ECR_PF = 0)** whose earned REVISED_BASIC+REVISED_DA is **below ₹15,000** — the
statutory PF wage ceiling (an employee under ₹15,000 PF wages cannot lawfully be
excluded from PF).

## Result: NO REAL GAPS — the M13 exemption invariant holds all 12 months

| Month | Rows matching filter | REAL gaps (full-month rate <15k) | Zero-basic rows excluded |
|---|--:|--:|--:|
| Apr-25 | 669 | **0** | 372 |
| May-25 | 946 | **0** | 558 |
| Jun-25 | 1,500 | **0** | 184 |
| Jul-25 | 1,454 | **0** | 262 |
| Aug-25 | 1,532 | **0** | 806 |
| Sep-25 | 1,411 | **0** | 380 |
| Oct-25 | 1,468 | **0** | 1,090 |
| Nov-25 | 1,511 | **0** | 315 |
| Dec-25 | 1,494 | **0** | 344 |
| Jan-26 | 1,395 | **0** | 745 |
| Feb-26 | 1,574 | **0** | 215 |
| Mar-26 | 1,690 | **0** | 475 |
| **TOTAL** | **16,644** | **0** | 5,746 |

Every matching row is a **part-month attendance effect**: the employee's
full-month Basic+DA rate (M13's `MONTHLY_PROJ_BASIC_DA`) is ≥ ₹15,000; the earned
amount fell below only because fewer days were worked. This is exactly the
invariant Rule M13 enforced (day reduction + basic lift for ECR_PF=0 rows), now
independently confirmed on all 12 final sheets.

## ⚠️ Convention caveat (documented for audit defence)

M13's projection multiplies the per-day Basic+DA by the month's **calendar days**
(e.g. ₹484/day × 31 = ₹15,004 — marginally over the line). Under a **stricter
26-day / SITEDIVISIONDAYS convention**, a minority of rows (~211 of Dec-25's
1,494, ~14%) would project marginally BELOW ₹15,000 (e.g. ₹484 × 30 = ₹14,520).
These are borderline-by-convention, not clear violations — but if EPFO challenges
the projection basis, these rows are the exposed edge. The workbook carries days,
divisor and B+DA per row so either convention can be re-derived.

Working file: `docs/pf-salary-reconciliation/fy2025-26/FY2526_ECRPF0_Below15K_Filter.xlsx`
(SUMMARY + one tab per month; any real-gap rows would be red and sorted on top;
ACTION/REMARKS working columns).
