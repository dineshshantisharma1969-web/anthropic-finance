# PF / ESI Salary Reconciliation — Merged **April + May 2026** (FY2026-27)

A single downloadable Excel workbook that merges the April 2026 and May 2026 PF
reconciliations into one "PF format", so both months can be reviewed and filed
side by side.

## File

| File | What it is |
|---|---|
| **`PF_Reconciliation_Apr_May_2026.xlsx`** | The merged workbook — download and open in Excel / Google Sheets. |
| `build_merged_xlsx.py` | Reproducible builder (`python3 build_merged_xlsx.py`). |

### Tabs in the workbook

1. **Overview** — both months' reconciliation anchors side by side, golden-rule status.
2. **Apr-2026 PF** — rule-group rollup (PF_ANCHOR / PF_SECONDARY / ESI_ONLY / NO_PF_NO_ESI), row-level PF audit, and checks & balances.
3. **May-2026 PF** — summary metrics, PF-rule mix, ESI-status mix, and ESI-exempt heads.
4. **Apr vs May** — month-over-month comparison of the reconciliation anchors (Δ and Δ%).

## Result — both months PASS

| Anchor (₹) | April 2026 | May 2026 |
|---|--:|--:|
| Total salary rows | 21,152 | 21,802 |
| Revised PF (= ECR anchor) | 25,221,042 | 26,378,587 |
| **PF gap (Revised − ECR)** | **0** | **0** |
| Revised ESI (= Future anchor) | 321,937 | 935,122 |
| Future ESI | 356,370 | 945,246 |
| Net drift | 0 | 0 |

Golden rules hold in both months: **Σ Revised PF = ECR filed (gap ₹0)** and
**Net Payable unchanged (drift ₹0)**.

## Sources

- **April 2026:** `April26_Reconciliation_Report.xlsx` (Summary rollup + row-verified
  PF_Audit), as captured in `../april-2026/reconciliation_data_April2026.json`.
- **May 2026:** `May26_RECONCILED_FINAL.xlsx` / `May26_Salary_Summary`
  (Google Drive `may-26` folder).

## Method note

Both months cover already-filed statutory periods, so the figures are immutable
source-of-record values (not a live model). Source anchors are shown in blue; the
bold black totals, gaps and month-over-month deltas are computed in the builder and
**asserted against each month's independent anchor** before the workbook is written
(e.g. Σ rule-group rows = total rows; Σ Revised PF = ECR PF; PF gap = 0). The
per-row May reconciliation file is ~18 MB (above the Drive download cap in this
environment); April NET and original-salary PF were not captured at summary level
in the April build and are shown as "—".
