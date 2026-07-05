# ESI Enrollment Audit — eligible-but-not-enrolled, all 12 months FY25-26

Filter (mirrors the PF ECR-0 audit): employees with **NO ESI contributed**
(ESIC = 0 AND REVISED_ESIC = 0) whose **full-month gross ≤ ₹21,000** (the ESI wage
ceiling) — i.e. ESI-eligible but not enrolled. Full-month gross projection used, so
part-month attendance dips are excluded (those whose full-month rate > ₹21k are
legitimately exempt and dropped). Verified: 0 false positives; ~2,280 exempt rows
correctly excluded in April alone.

## Result — the enrollment gap and its cost

| Month | ESI-eligible but NOT enrolled | Exposure @ 4%/month (₹) |
|---|--:|--:|
| Apr-25 | 782 | 3,20,027 |
| May-25 | 334 | 1,41,498 |
| Jun-25 | 234 | 84,492 |
| Jul-25 | 251 | 74,143 |
| Aug-25 | 322 | 84,845 |
| Sep-25 | 186 | 44,213 |
| Oct-25 | 449 | 70,780 |
| Nov-25 | 356 | 85,899 |
| Dec-25 | 320 | 72,460 |
| Jan-26 | 281 | 1,03,033 |
| Feb-26 | 290 | 1,18,167 |
| Mar-26 | 345 | 1,43,114 |
| **TOTAL (sum of months)** | **4,150 row-instances** | **₹13,42,671 /yr of monthly exposures** |

- **Distinct employees** flagged over the year: **2,793**
- **Persistent (not enrolled ≥3 months): 284** — the priority enrollment list;
  every month unenrolled is a fresh statutory default (EE 0.75% + ER 3.25%).
- April is the spike (782) — likely new-year joiners not yet enrolled; the run-rate
  settles to ~250–350/month. Enrollment discipline is imperfect but not worsening.

## Exposure basis
ESI = **4% of gross** (EE 0.75% + ER 3.25%). Under-enrolment is an employer default:
ESIC can demand contributions + interest + damages for the un-enrolled period, so
the persistent-284 list is the real risk and should be enrolled first.

## ⚠️ Reconciliation note vs the monthly worklists
The monthly `SUMMARY_<Mon>` ESI counts (e.g. Apr 590) used a **fixed-rate** basis
(FIXEDGROSS × 26). This audit uses the **gross-projection** basis, which is the
correct test for ESI (a gross-wage levy), so counts differ (Apr 782 vs 590). Treat
THIS audit as the authoritative ESI-enrollment view.

Working file: `docs/pf-salary-reconciliation/fy2025-26/FY2526_ESI_Enrollment_Audit.xlsx`
(SUMMARY + one tab per month; every row = a genuine gap, red, with ESIC/UAN numbers,
EE/ER amounts, ACTION/REMARKS columns — hand straight to the enrollment team).
