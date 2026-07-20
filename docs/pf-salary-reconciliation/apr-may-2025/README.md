# PF / ESI Salary Reconciliation — Merged **April + May 2025** (FY2025-26)

A single downloadable Excel workbook that merges the April 2025 and May 2025 PF
reconciliations (v3 CORRECTED) into one "PF format", side by side.

## File

| File | What it is |
|---|---|
| **`PF_Reconciliation_Apr_May_2025.xlsx`** | The merged workbook — download and open in Excel / Google Sheets. |
| `build_merged_xlsx.py` | Reproducible builder (`python3 build_merged_xlsx.py`). |

### Tabs

1. **Overview** — both months' anchors side by side, golden-rule status, and the PF bridge (booked vs reconciled).
2. **Apr-2025 PF** — full v3 summary: anchors, invariant status (0 violations), lift/relax counts, totals.
3. **May-2025 PF** — same structure.
4. **Apr vs May** — month-over-month comparison of the reconciliation figures (Δ and Δ%).

## Result — both months PASS

| Anchor (₹) | April 2025 | May 2025 |
|---|--:|--:|
| Total salary rows | 19,161 | 19,327 |
| Revised PF (= ECR filed) | 2,28,55,004 | 2,29,77,657 |
| **PF gap (Revised − ECR)** | **0** | **0** |
| Revised ESI (= Future) | 8,47,126 | 9,23,563 |
| **ESI gap (Future − Revised)** | **0** | **0** |
| Net payable (= Revised Net) | 22,96,89,886 | 23,21,02,234 |
| Net drift | 0 | 0 |

Golden rules hold in both months: **Σ Revised PF = ECR filed (gap ₹0)**,
**Σ Revised ESI = Future (gap ₹0)**, and **Net Payable unchanged (drift ₹0)**.
All invariants report 0 violations.

## PF bridge

| Line (₹) | April 2025 | May 2025 |
|---|--:|--:|
| PF booked (salary sheet, incl back-office) | 2,41,73,582 | 2,46,10,756 |
| Reconciled PAN PF (= ECR filed) | 2,28,55,004 | 2,29,77,657 |
| **Back-office PF (booked − reconciled)** | **13,18,578** | **16,33,099** |

## Sources

- **April 2025:** `Apr25_Reconciliation_Report.xlsx` — Summary tab (v3 CORRECTED).
- **May 2025:** `May25_Reconciliation_Report_PROJ_CAPPED.xlsx` — Summary tab (v3 CORRECTED).
- **PF-booked cross-reference:** `../SUMMARY_FY2025-26.csv` (Apr-25 / May-25 rows).
  NET ties exactly across both sources.

## Method note

Both months cover already-filed statutory periods, so the figures are immutable
source-of-record values. Source anchors are shown in blue; bold black figures
(back-office PF, deltas) are computed in the builder and **asserted against each
month's anchor** before writing (PF gap = 0, ESI gap = 0, NET diff = 0, invariant
violations = 0).
