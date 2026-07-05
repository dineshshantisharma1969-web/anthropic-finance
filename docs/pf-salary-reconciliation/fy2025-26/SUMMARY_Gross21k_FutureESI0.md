# Filter: gross ≤ ₹21,000 AND ESIC AS PER FUTURE = 0 — monthwise counts (all 12 months)

Filter on each monthly M13 sheet: **earned GROSS AMT ≤ ₹21,000** AND **ESIC AS PER
FUTURE = 0** (the statutory ESI anchor — Golden Rule: REVISED_ESIC = ESIC AS PER
FUTURE). These are employees below the ESI ceiling with zero statutory (future-basis)
ESI. Note: uses EARNED gross (as shown in the sheet), so counts are higher than the
full-month-projection enrollment audit. (Nov-25/Dec-25 spell the column
`ESIC_AS_PER_FUTURE`; both spellings handled.)

## Monthwise count (the number only, as requested)

| Month | Employees (gross ≤ ₹21k & Future-ESI = 0) | Exposure 4%/mo (₹) |
|---|--:|--:|
| Apr-25 | **1,780** | 9,05,969 |
| May-25 | **1,442** | 8,18,889 |
| Jun-25 | **1,602** | 7,34,267 |
| Jul-25 | **1,523** | 6,85,565 |
| Aug-25 | **1,632** | 6,62,906 |
| Sep-25 | **1,343** | 5,74,697 |
| Oct-25 | **1,773** | 6,08,210 |
| Nov-25 | **1,862** | 8,28,328 |
| Dec-25 | **1,709** | 7,96,392 |
| Jan-26 | **1,287** | 7,62,962 |
| Feb-26 | **1,305** | 7,98,140 |
| Mar-26 | **1,444** | 8,62,659 |
| **TOTAL (row-instances)** | **18,702** | **₹90.4L** |

Per-employee detail (names/ESIC/UAN) is in the workbook's monthly tabs:
`docs/pf-salary-reconciliation/fy2025-26/FY2526_Gross21k_FutureESI0_Filter.xlsx`.
Bot answers the counts above (e.g. "gross under 21000 future ESI zero July" → 1,523).
