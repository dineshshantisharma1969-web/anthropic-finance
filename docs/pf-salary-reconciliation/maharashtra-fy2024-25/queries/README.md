# Enquiry results — "Basic < ₹15,000 & ECR PF = 0" (FY2024-25)

Pre-computed answers for the Telegram/n8n enquiry: employees in the salary sheet with
**Basic(+DA) below ₹15,000** and **no ECR/challan PF filed** (`REVISED_PF = 0`), split by
attendance. Generated from `../corrected_monthly/CORRECTED_<MONTH>.csv`.

| File | What it is |
|---|---|
| `SUMMARY_below15k_ecr0_partVSfull_FY2024-25.csv` | Month-wise counts + PF parked, part-days vs full-attendance |
| `<MONTH>_below15k_partdays_ecr0.csv` | Part-days rows (low basic because worked < full standard month) |
| `<MONTH>_below15k_FULLdays_GAP_ecr0.csv` | **Full-attendance rows — the compliance-gap flag** (worked the full standard month, monthly basic still below ₹15,000, yet not in ECR) |

## How to read the two sets

- **Part-days**: `NORMALDAYS (W/DAYS) < M/DAYS (divisor)` (NCP > 0). Basic is low mainly because
  fewer days were worked; the reconciliation reduces `ADJ_WORKING_DAYS` so the full-calendar-month
  projection clears ₹15,000, making the PF-absence self-consistent.
- **Full-attendance GAP**: `W/DAYS = M/DAYS`, `NCP = 0`. The employee worked the full standard month,
  yet the monthly basic is still below the ₹15,000 PF ceiling and no ECR was filed — the clearest
  candidate for a PF-coverage review. (Most are the ₹13,275 @ 26-day sites.)

**Year totals:** 889 below-15k not-in-ECR employee-months → 557 part-days · **332 full-attendance
(gap flag)**.
