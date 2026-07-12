# ISPL Salary Audit FY 2025-26 — Monthly Salary Sheet Summary (all deduction columns)

Month-wise totals of the 12 monthly salary sheets (`*_M13_FINAL.xlsx`, sheet "Salary (Corrected)")
from Drive folder `ISPL SALARY AUDIT 25-26/fy2025-26/ESI_WASHING_REALLOCATED`.

Column order follows the requested layout: **REVISED GROSS → REVISED GROSS NEW → all deduction
columns → REVISED TOTAL DEDUCTION → REVISED NET PAYABLE → ORIGINAL NETPAYABLE → NET Δ → OT /
FESTIVAL HOLIDAY / NATIONAL (PAID) HOLIDAY blocks (amount, ESIC, net).**

The two `NET` proof columns confirm the sacrosanct rule: **REVISED NET PAYABLE equals the ORIGINAL
NETPAYABLE (as paid to employees) to the rupee — NET Δ = ₹0 every month**, and ₹0 for the FY total.

## Files

| File | Contents |
|---|---|
| `Monthly_Salary_Deductions_Summary_FY2025-26.xlsx` | Full workbook: Monthly_Summary, Checks, Source_Mapping, AllColumns_Detail, README |
| `Monthly_Summary_FY2025-26.csv` | Month-wise summary incl. TOTAL row |
| `Checks_FY2025-26.csv` | GROSS − TOTAL DED vs NET PAYABLE per month |
| `Source_Mapping_FY2025-26.csv` | Which source column fed each summary figure, per month |
| `AllColumns_Detail_FY2025-26.csv` | Sum of every numeric column of every monthly sheet |
| `month_column_sums_raw.json` | Raw per-month headers + column sums (audit trail) |
| `Earnings_Deductions_Summary_FY2025-26.xlsx` / `.csv` | Earnings-side summary: revised basic + DA + every allowance column, then the full deduction block, net-payable proof |
| `dashboard_FY2025-26.html` | Interactive audit dashboard (also published as a Claude artifact) |

A Google-Sheet copy (`Monthly_Salary_Deductions_Summary_FY2025-26`) lives in the same Drive folder
as the monthly files.

## Method

The monthly files (~20 MB each) exceed direct-download limits, so each was copied server-side to a
temporary Google Sheet (Drive `files.copy` with conversion), a row of `=SUM()` formulas was written
over the header row of the throwaway copy, the computed totals were read back via the Sheets API,
and the temp copy was deleted. Orchestrated through the user's n8n instance
(workflow "ISPL Month Column Sums (via Sheets formulas)"). Originals were never modified.

## Column mapping notes (see Source_Mapping for the full matrix)

- Header row position and column sets differ by month (223–264 columns).
- Apr/May-25 carry a revised deduction detail block (".1" columns). Jun-25 has the block but blank —
  original deduction columns used instead (they are unchanged by the reconciliation passes).
- ESIC (REVISED) = `ESIC.1` for Apr–Jul-25, `REVISED_ESIC` for Aug-25 onward.
- OTHER DEDUCTION (REVISED) is the plug column (`OTHER_DEDUCTION` / `REVISED_OTHER_DEDUCTION`) that
  absorbs PF/ESI differences per the PF-salary-reconciliation rules (NET PAYABLE never changes).

## Checks & balances

- **Net payable preserved (golden rule):** `ORIGINAL NETPAYABLE − REVISED NET PAYABLE = ₹0` for
  every month and for the FY total (₹293,29,89,494 = ₹293,29,89,494). All PF/ESI adjustments are
  absorbed into the OTHER DEDUCTION plug, so what reached employees never changed.
- `REVISED GROSS − REVISED TOTAL DEDUCTION` vs `REVISED NET PAYABLE`: within ±₹365/month
  (stored-value rounding *inside* the revised block; consistent with the C2 tolerance in the
  reconciliation skill — cosmetic, not a change to what was paid).
- REVISED PF and REVISED NET PAYABLE totals for **all 12 months exactly match** the
  `PF_ESI_Reco_Summary_FY2025-26` produced in the morning session (e.g. Apr-25 PF ₹2,29,80,428 /
  NET ₹22,96,89,886 … Mar-26 PF ₹2,58,44,828 / NET ₹26,35,30,256).

## FY 2025-26 totals

| Measure | Total |
|---|---|
| REVISED GROSS | ₹437,65,52,661 |
| REVISED GROSS NEW | ₹376,68,66,693 |
| PF (REVISED) | ₹29,17,58,299 |
| ESIC (REVISED) | ₹1,84,65,975 |
| REVISED TOTAL DEDUCTION | ₹144,35,65,364 |
| REVISED NET PAYABLE | ₹293,29,89,494 |
| ORIGINAL NETPAYABLE | ₹293,29,89,494 |
| NET Δ (Orig − Revised) | ₹0 |
| NET OT | ₹11,78,54,765 |
| FESTIVAL HOLIDAY NET | ₹41,63,785 |
| NATIONAL/PAID HOLIDAY NET | ₹71,16,268 |
