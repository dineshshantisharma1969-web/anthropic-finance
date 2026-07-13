# 12-Month Consolidation — Revised Block (GC:HK), FY 2025-26

Row-level merge of the revised block (**ADJ_WORKING_DAYS → REVISED_NET_PAYABLE**, i.e. columns
GC:HK of Apr-25, matched **by header name** in every other month since positions/sets change),
plus site/employee IDs and original NETPAYABLE, from all 12 `*_M13_FINAL.xlsx` sheets.

| File | Contents |
|---|---|
| `CONSOL_FY2025-26_RevisedBlock.csv.gz` | Consolidated file: 235,082 rows × 42 cols (gunzip to open) |
| `PIVOT_Month_Summary.csv` | Pivot: rows = MONTH, values = SUM of every numeric column |
| `PIVOT_State_x_Month_NetPayable.csv` | Pivot: SITESTATE × MONTH, SUM(REVISED_NET_PAYABLE) |
| `PIVOT_12M_Summary_FY2025-26.xlsx` | Both pivots, formatted, + README |
| `Consolidate_ISPL_Salary.bas` | VBA macro to reproduce merge + PivotTable in Excel locally |

Google-Sheet copy of the pivots: `PIVOT_12M_Summary_RevisedBlock_FY2025-26` in the
ESI_WASHING_REALLOCATED Drive folder.

**Checks:** monthly & FY `REVISED_NET_PAYABLE` match the audited figures exactly
(FY ₹293,29,89,494); row-level original vs revised net payable differs in **0 of 235,082 rows**.
PT/LWF/etc. sub-columns exist inside the block only in Apr–Jun-25 sheets (blank elsewhere).

Method: per month, a temp converted Google Sheet copy was slimmed server-side
(batchUpdate deleteDimension) to the keep-columns, exported as CSV (<10 MB), merged with pandas;
temp copies deleted. Originals untouched.

## PF basis (final, 13-Jul-2026 IST)

**Salary-sheet PF = filed ECR PF, per employee, all 12 months** — verified against the merged ECR
FORMAT challan files. Headline: Apr-25 ₹2,29,80,428 … FY ₹29,17,54,961 (after the June corrected
copy `June_M13_FINAL_PF-ECR-CORRECTED`: −₹4,196 unremitted PF removed, +₹858 BISWAJIT DHAR added;
net payable unchanged). The earlier matched figure (Apr ₹2,29,58,913 / FY ₹29,11,52,447) was the
**02-Jul pre-fix snapshot**, superseded by the 03-Jul `Fix-RevisedPF-M13` apply run that pulled
ECR-paid Back-Office-group employees' PF into the sheets. Bridge to total ECR EE (₹29,55,70,456,
ties to the EPF challan register to the rupee) is on the PF_Tieout tab.
