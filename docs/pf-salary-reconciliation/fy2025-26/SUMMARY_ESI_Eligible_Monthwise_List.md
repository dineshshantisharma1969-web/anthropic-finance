# ESI-Eligible Employee List (full-month gross ≤ ₹21,000) — monthwise, all 12 months

Every employee whose **full-month gross ≤ ₹21,000** (the ESI wage ceiling), one tab
per month, with an `IN ESI NOW? (Y/N)` flag (green = contributing, red = not enrolled).
Employee data only. Built from the deployed 'Salary (Corrected)' sheet.

## Monthwise counts

| Month | Employees full-month ≤ ₹21k | In ESI | NOT in ESI (enroll) |
|---|--:|--:|--:|
| Apr-25 | 7,583 | 6,801 | 782 |
| May-25 | 7,175 | 6,841 | 334 |
| Jun-25 | 9,706 | 9,472 | 234 |
| Jul-25 | 9,978 | 9,727 | 251 |
| Aug-25 | 9,524 | 9,202 | 322 |
| Sep-25 | 10,145 | 9,959 | 186 |
| Oct-25 | 8,802 | 8,353 | 449 |
| Nov-25 | 10,889 | 10,533 | 356 |
| Dec-25 | 10,670 | 10,350 | 320 |
| Jan-26 | 7,531 | 7,250 | 281 |
| Feb-26 | 7,844 | 7,554 | 290 |
| Mar-26 | 7,411 | 7,066 | 345 |

- The ≤₹21k band is the bulk of the deployed workforce (7k–11k/month).
- ~96–98% are already in ESI each month; the **NOT-in-ESI subset** (186–782/month)
  is the enrollment gap (detail with names/ESIC/UAN in `FY2526_ESI_Enrollment_Audit.xlsx`).
- June–December headcount runs highest (peak-season deployment); Jan–Mar lower.

## How to access
- **Full employee-by-employee roster** → open
  `docs/pf-salary-reconciliation/fy2025-26/FY2526_ESI_Eligible_Monthwise_List.xlsx`
  (SUMMARY + 12 monthly tabs). Opens in the mobile Excel app after `git pull`.
- **Bot (mobile)** answers the counts above — e.g. "how many employees full-month
  under 21000 in April" → 7,583; "how many not in ESI in October" → 449. It does
  NOT read out the full row list (too large — that's the Excel).
