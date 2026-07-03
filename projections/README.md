# FY 2026-27 Projections — Impressions Services Private Limited

**Base:** `BS _TB _2025-26 CONSOLIDATED_set2.xlsx` (Drive › CORRECTED SALARY FOLDER 25-26), FY 2025-26 columns of the `pl` and `BS` sheets.

**Deliverable:** `PROJECTIONS_FY2026-27_BS_PL_set2.xlsx` — 4 sheets: Assumptions, Projected P&L FY27, Projected BS FY27, Summary & Ratios. All projected cells are live formulas driven by the growth rate in `Assumptions!C6` (set to 10%).

## Method

Revenue from operations grown **+10%**; all variable/operating items scaled proportionately; prudence overrides applied:

1. **Other income held flat** at the FY 2025-26 level (not grown).
2. **Change in inventories taken as nil** — no stock gain assumed.
3. **Full current tax provided at 25.168%** (s.115BAA incl. surcharge & cess). FY 2025-26 reported PAT (₹17.08 Cr) benefited from a prior-year tax reversal of ₹2.97 Cr; the projection assumes no such credit recurs.
4. **No dividend** — entire PAT retained in reserves.
5. **Borrowings held at FY26 levels** — incremental working capital funded from internal accruals; cash & bank is the balancing figure.
6. **Gratuity (long-term provision) grown with employee cost** (+10%).

## Headline projected figures (₹ Crore)

| Metric | FY 2025-26 | FY 2026-27 (Proj) |
|---|---:|---:|
| Revenue from operations | 489.82 | 538.81 |
| Total expenses | 476.71 | 524.38 |
| Profit before tax | 14.11 | 15.43 |
| Profit after tax | 17.08* | 11.54 |
| Net worth (incl. interunit) | 147.40 | 158.95 |
| Total borrowings (LT + ST) | 43.81 | 43.81 |
| Trade receivables | 166.56 | 183.22 |
| Cash & cash equivalents | 4.81 | 2.31 |
| Balance sheet total | 259.47 | 277.84 |
| Current ratio | 2.28x | 2.33x |
| Debt / equity | 0.30x | 0.28x |

\* FY 2025-26 PAT exceeds PBT due to the prior-year tax reversal; projected PAT is lower than the base year only because full tax is provided per prudence.

`build_projections.py` regenerates the workbook from the base figures.
