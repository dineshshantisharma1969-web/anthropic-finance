# PF / ESI Salary Reconciliation — Checks & Balances
## ISPL (Impressions Services) · FY2025-26 · M13 FINAL

> **Scope:** Full-year FY2025-26 — 12 reconciled monthly payrolls plus the **M13** annual true-up. Validated against the `pf-salary-reconciliation` skill (Golden Rules + validation set C1–C10). Figures are sourced from the already-built monthly reconciliation (summary / pivot / Tally-ledger workbooks); the per-row 18–20 MB monthly files exceed the 10 MB Drive download cap, so verification is performed at the month-aggregate level and against the per-row invariants already asserted in the M13 FINAL report.

**Result:** 7 PASS · 5 REVIEW · 0 FAIL (14 checks). No FAILs — all golden-rule invariants hold; REVIEW items are cross-build/source reconciliation notes, not errors in the reconciled book.

---
## 1. Golden Rules (skill invariants)

| Rule | Status | Detail |
|---|---|---|
| Golden Rule 1 — Σ REVISED_PF = ECR_PF (per-employee, ₹0 gap) | ✅ PASS | M13 FINAL asserts 0 drift on all 12 months. Reconciled PAN PF = ₹290,652,769 is the ECR-filed anchor. |
| Golden Rule 3 — NET PAYABLE unchanged (REVISED_NET = NETPAYABLE) | ✅ PASS | M13 FINAL: NET drift ALL ZERO (row & total) across all 12 months + M13. |
| Golden Rule 2 — Σ REVISED_ESIC = Future-sheet ESIC | ✅ PASS | M13 FINAL: 0 drift. Future-basis ESI anchor = ₹18,693,848. |

## 2. Arithmetic foot-checks (month-aggregate)

| Check | Status | Detail |
|---|---|---|
| Net Payable = Total Earned Gross − Total Deduction (every month) | ✅ PASS | All 12 months foot to the rupee. |
| Total Deduction = PF + ESI + PT + Other Deductions (every month) | ✅ PASS | All 12 months foot to the rupee. |
| Σ(12 months) reconciles to the published TOTAL row | ✅ PASS | All 9 columns tie out. |
| PF reconciliation bridge (booked → reconciled → Tally) | ℹ️ INFO | Booked PF incl back-office ₹307,072,360 = Reconciled PAN PF ₹290,652,769 + Back-office PF ₹16,419,591. Tally EPF payable ledger = ₹296,746,845. |
| Bridge foots: Reconciled PAN PF + Back-office PF = Booked PF | ✅ PASS | 290,652,769 + 16,419,591 = 307,072,360 vs booked 307,072,360. |

## 3. Cross-source reconciliation & review items

| Item | Status | Detail |
|---|---|---|
| Cross-check: Net total across summary builds | ⚠️ REVIEW | Monthly = Pivot = ₹2,932,971,946 (agree). M13_SUMMARY build = ₹2,931,995,085 → short by ₹976,861, isolated to October (₹241,289,007 vs authoritative ₹242,265,868). M13_SUMMARY appears to have used a pre-final October build; use the pivot/monthly figure. |
| Cross-check: reconciled PAN PF across summary builds | ⚠️ REVIEW | Pivot (ECR anchor) = ₹290,652,769. M13_SUMMARY = ₹290,651,911 → short by ₹858, isolated to June (₹23,278,054 vs ₹23,278,912). Treat the pivot/ECR figure as authoritative. |
| Cross-check: ESI basis (Future vs M13_SUMMARY) | ⚠️ REVIEW | Future-basis (anchor) = ₹18,693,848; M13_SUMMARY pre-merge basis = ₹18,466,035 (Δ ₹227,813). The Future-basis figure is the statutory anchor. |
| Cross-check: M13+CL/Bonus merged Net vs Tally Salary Payable | ⚠️ REVIEW | M13+CL merged REVISED_NET = ₹3,194,063,202 vs Tally 'SALARY PAYABLE-2025-26' = ₹3,194,048,568 → Δ ₹14,634 (≈0.0005%). Immaterial; reconciles within rounding of the bonus/leave merge. |
| M13 exceptions (DA alone exceeds ECR_PF/0.12 — exact 12% cannot hold) | ℹ️ INFO | 2 exception rows total (Sep 1, Feb 1) — basic clamped, listed in PF_M13_Exceptions_Review.xlsx. All other rows satisfy REVISED_PF = 12%(BASIC+DA). |
| Anomaly flag — Jan/Feb gross ≈ 2× run | ⚠️ REVIEW | Source note: Jan-26 & Feb-26 gross ~2× other months on same headcount — possible double/bonus run in those source files. Net Payable still ties; verify before statutory filing. |

## 4. Consolidated month-wise summary

All figures in ₹. `PF_booked` includes back-office; the **reconciled PAN PF = ECR** anchor is ₹290,652,769.

| Month | Basic+DA | Other Allow | Earned Gross | PF (booked) | ESI | PT | Other Ded | Total Ded | Net Payable |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Apr-25 | 210,043,740 | 53,423,443 | 263,467,183 | 24,173,582 | 1,489,009 | 631,048 | 7,483,658 | 33,777,297 | 229,689,886 |
| May-25 | 209,829,942 | 54,053,636 | 263,883,578 | 24,610,756 | 1,505,739 | 668,332 | 4,996,518 | 31,781,344 | 232,102,234 |
| Jun-25 | 209,550,065 | 55,672,396 | 265,222,461 | 24,904,423 | 1,518,775 | 657,648 | 5,202,922 | 32,283,768 | 232,938,693 |
| Jul-25 | 216,450,960 | 57,832,758 | 274,283,718 | 25,695,497 | 1,569,237 | 681,438 | 5,242,616 | 33,188,788 | 241,094,930 |
| Aug-25 | 211,723,679 | 58,249,306 | 269,972,986 | 25,208,736 | 1,540,847 | 680,314 | 5,373,555 | 32,803,452 | 237,169,533 |
| Sep-25 | 215,604,615 | 59,856,339 | 275,460,954 | 25,684,018 | 1,574,933 | 691,456 | 7,020,570 | 34,970,977 | 240,489,977 |
| Oct-25 | 201,092,730 | 73,570,730 | 274,663,460 | 24,362,599 | 1,544,260 | 702,917 | 5,787,816 | 32,397,592 | 242,265,868 |
| Nov-25 | 211,826,625 | 59,928,929 | 271,755,554 | 25,168,592 | 1,536,582 | 687,847 | 4,672,355 | 32,065,376 | 239,690,178 |
| Dec-25 | 226,034,081 | 64,620,891 | 290,654,972 | 26,592,067 | 1,611,674 | 723,248 | 4,824,198 | 33,751,187 | 256,903,785 |
| Jan-26 | 228,650,533 | 64,623,148 | 293,273,681 | 26,840,187 | 1,625,762 | 715,246 | 4,603,570 | 33,784,765 | 259,488,916 |
| Feb-26 | 226,809,311 | 65,702,072 | 292,511,383 | 26,750,772 | 1,616,147 | 865,325 | 5,671,449 | 34,903,693 | 257,607,690 |
| Mar-26 | 231,077,269 | 66,925,374 | 298,002,643 | 27,081,131 | 1,646,232 | 728,379 | 5,016,645 | 34,472,387 | 263,530,256 |
| **TOTAL** | **2,598,693,550** | **734,459,022** | **3,333,152,573** | **307,072,360** | **18,779,197** | **8,433,198** | **65,895,872** | **400,180,626** | **2,932,971,946** |

## 5. PF reconciliation bridge

| Line | ₹ |
|---|--:|
| Reconciled PAN PF (= ECR filed, golden-rule anchor) | 290,652,769 |
| + Back-office PF | 16,419,591 |
| = Booked PF (salary sheets) | 307,072,360 |
| Tally EPF-Employee-Share payable ledger | 296,746,845 |

## 6. M13 rule-application statistics

Rule **M13**: PF = 12% on (BASIC+DA). `ECR_PF>0` → REVISED_BASIC = ECR/0.12 − DA (plug to attendance allowance; GROSS/PF/NET held). `ECR_PF=0` → project (BASIC+DA)×FULL_MONTH/ADJ_DAYS > 15000 via day reduction then basic lift; absorbed by attendance allowance, else OTHER_DEDUCTION.

| Month | Active | Rule A 12%(B+DA) | Rule B day-adj | B→att | B→OD | NET drift | GROSS↑(OD) | Exceptions |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| Apr-25 | 18794 | 2355 | 111 | 3 | 0 | 0 | 0 | 0 |
| May-25 | 18774 | 2443 | 197 | 0 | 0 | 0 | 0 | 0 |
| Jun-25 | 18754 | 2547 | 1143 | 0 | 0 | 0 | 0 | 0 |
| Jul-25 | 18905 | 2577 | 974 | 3 | 0 | 0 | 0 | 0 |
| Aug-25 | 18626 | 2520 | 1103 | 3 | 0 | 0 | 0 | 0 |
| Sep-25 | 18830 | 2671 | 1055 | 1 | 0 | 0 | 0 | 1 |
| Oct-25 | 18699 | 2606 | 211 | 0 | 1 | 0 | 1 | 0 |
| Nov-25 | 18986 | 2928 | 211 | 636 | 0 | 0 | 0 | 0 |
| Dec-25 | 19460 | 3192 | 217 | 664 | 3 | 0 | 3 | 0 |
| Jan-26 | 19624 | 3286 | 841 | 341 | 0 | 0 | 0 | 0 |
| Feb-26 | 19649 | 3349 | 770 | 311 | 2 | 0 | 2 | 1 |
| Mar-26 | 20279 | 3378 | 848 | 406 | 0 | 0 | 0 | 0 |
| **TOTAL** | **229380** | **33852** | **7681** | **2368** | **6** | **0** | **6** | **2** |

## 7. M13 + CL/Bonus merged

| Line | ₹ |
|---|--:|
| Merged Gross (M13 + OT + Festival/National holiday) | 4,652,522,768 |
| Bonus | 27,773,882 |
| Leave encashment | 44,261,081 |
| Merged Revised Net Payable | 3,194,063,202 |
| Tally Salary Payable 2025-26 | 3,194,048,568 |

---
*Generated by `docs/pf-salary-reconciliation/build.py`. Open `dashboard.html` for the interactive view. See repo for source-file IDs.*