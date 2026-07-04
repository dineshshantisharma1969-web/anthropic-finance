# April 2026 — Excess Salary Triage (₹5.45 Cr flagged → what's actually real)

Triaged 2026-07-04 from `April26_RECONCILED_FINAL_M12_M15.xlsx` (4,974 ACTION_NEEDED=Y rows).

## Headline finding

**The ₹5,44,58,591 flagged "excess salary" is NOT ₹5.45 Cr of cash overpaid.**
Real cash overpayment can never exceed what was actually paid (gross). Capping each row's
excess at its actual gross gives a **maximum real cash exposure of ₹1,92,18,683** — and most
of that is a compliance issue (ESI), not overpayment.

| Bucket | Rows | Flagged excess | Actual gross paid | Cash-capped excess | Verdict |
|---|--:|--:|--:|--:|---|
| LOW ATTENDANCE (0–2 days) | 257 | 2,40,53,613 | 2,20,554 | **2,08,829** | 🟢 **~99% projection artifact** — 225/257 rows have "excess" > total pay. Tiny day-counts explode the full-month projection formula. Nobody was paid these amounts. |
| ESI-EXEMPT but eligible | 1,940 | 1,82,85,546 | 3,84,61,777 | 99,39,352 | 🟠 **Not overpayment — compliance gap.** 1,940 employees with real full-month rate ≤ ₹21,000 kept out of ESI. Exposure ≈ **₹15,38,471/month** in contributions (EE 0.75% ₹2.88L + ER 3.25% ₹12.50L) + retro/penalty risk. |
| PAID ABOVE FIXED RATE | 2,458 | 1,01,47,522 | 5,57,52,114 | **87,54,602** | 🔴 **The genuine review bucket.** Median only ₹2,437/row; OT + attendance allowance explains ~₹9.9L. **164 rows > ₹10k = ₹31.2L** — that's where the money is. |
| IMPLIED FULL-MONTH ≫ rate | 319 | 19,71,910 | 32,66,383 | 3,15,900 | 🟡 Mostly artifact (100/319 rows excess > gross); small residue folded into review list. |
| **TOTAL** | **4,974** | **5,44,58,591** | **9,77,00,828** | **1,92,18,683** | |

## Concentration

- **West Bengal** dominates the artifact bucket: ₹2.55 Cr of flagged excess (mostly 0–1 day rows at CBRE / Cushman & Wakefield / JLL Kolkata sites — new joiners/leavers mid-month).
- **ESI gap by client (headcount):** JLL 449 · CBRE 446 · Snow White 157 · Nestlé 143 · Ministry of Railways 133 · C&W 101 · SMS India 59.
- **Genuine-overpaid by client (₹):** review file 1 is sorted; JLL, Ministry of Railways and CBRE lead.

## Working files (in this folder)

| File | Rows | Use |
|---|--:|---|
| `REVIEW_1_overpaid_above_10k.csv` | **133** | 🔴 **START HERE** — overpayment candidates > ₹10k each (≈ ₹31L). Verify against attendance/OT approvals; recover or regularise. |
| `REVIEW_2_overpaid_all.csv` | 2,777 | Full overpaid-vs-rate population (median ₹2.4k — batch-review below ₹10k). |
| `REVIEW_3_ESI_enrollment_needed.csv` | 1,940 | Grouped by client — enroll in ESI from May-26 payroll; assess retro liability. |
| `REVIEW_4_projection_artifacts.csv` | 257 | Confirm these are joiners/leavers, then close as artifact. **Fix:** skip/cap the projection when NORMALDAYS ≤ 2 (or cap EXCESS at GROSS) in the next build. |

## Recommended decisions

1. **Close the ₹2.4 Cr artifact bucket** after a spot-check of 10 rows (all will show 0–1 days worked, sub-₹1k pay). Patch the excess formula: `EXCESS_SALARY = min(EXCESS_SALARY, GROSS AMT)` and suppress the flag when `NORMALDAYS ≤ 2`.
2. **ESI:** decide enrolment for the 1,940 from May-26 payroll (₹15.4L/month run-rate exposure grows every month it's open).
3. **Overpayment:** work `REVIEW_1` (133 people, ₹31L) first — 80% of the recoverable value in 3% of the rows.
