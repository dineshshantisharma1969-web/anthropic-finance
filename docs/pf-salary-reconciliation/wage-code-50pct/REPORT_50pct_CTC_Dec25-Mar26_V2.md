# 50% CTC Rule Check — ISPL, Dec-25 to Mar-26 (M13 FINAL **V2** sheets)

Run date: 2026-07-17 · Requested by dinesh@impressionsgroup.in
Source: `ISPL SALARY AUDIT 25-26 / SALARY FOLDER 2025-26 / M13_FINAL_EXTRACTED /`
`December|January|February|March_M13_FINALV2.xlsx` — first tab **"Salary (Corrected) (4)"** (header on row 2).

## Test applied (as requested)

Per employee row:

```
DIFF = CTC − (FIXED_BASIC + FIXED_DA)
VIOLATION if DIFF > 50% of CTC          (i.e. fixed basic+DA is less than half of CTC)
```

Amounts shown in separate columns of the output files:

| Column | Meaning |
|---|---|
| `FIXED_BASIC_PLUS_DA` | FIXED_BASIC + FIXED_DA |
| `DIFF_CTC_MINUS_BASIC_DA` | CTC − (FIXED_BASIC + FIXED_DA) — for every row |
| `DIFF_PCT_OF_CTC` | that diff as % of CTC |
| `VIOLATION_50PCT` | Y/N flag |
| `VIOLATION_DIFF_AMOUNT` | the diff amount, filled **only** on violating rows |
| `EXCESS_ABOVE_50PCT_OF_CTC` | how much the diff exceeds the 50%-of-CTC limit (= amount by which basic+DA falls short of 50% of CTC) |

Rows with CTC = 0/blank are never flagged (counted in `employee_rows` but not testable).

## Results

| Month | Employee rows | Rows with CTC | **Violations** | % of rows | **Σ DIFF on violators (₹)** | **Σ excess above 50% (₹)** | Σ CTC of violators (₹) |
|---|--:|--:|--:|--:|--:|--:|--:|
| Dec-25 | 19,800 | 19,453 | **2,781** | 14.05% | 4,50,62,345 | 1,67,04,665 | 5,67,15,361 |
| Jan-26 | 20,364 | 19,623 | **2,788** | 13.69% | 4,56,06,971 | 1,65,36,442 | 5,81,41,059 |
| Feb-26 | 19,862 | 19,648 | **2,930** | 14.75% | 4,44,89,181 | 1,57,43,613 | 5,74,91,137 |
| Mar-26 | 20,749 | 20,279 | **3,163** | 15.24% | 4,89,83,687 | 1,77,52,206 | 6,24,62,961 |
| **Total (employee-months)** | **80,775** | **79,003** | **11,662** | **14.44%** | **18,41,42,184** | **6,67,36,926** | **23,48,10,518** |

Counts are employee-month rows (the same employee failing in all four months is counted four times).

## Top recurring violators (by DIFF, appear in every month's top-10)

| EMPCODE | Name | Site | CTC (Dec) | Basic+DA | DIFF | % of CTC |
|---|---|---|--:|--:|--:|--:|
| 24080407 | USHA SHONSHON KHAPUDANG | HYATT SERVICES INDIA | 1,62,028 | 38,000 | 1,24,028 | 76.6% |
| 25091128 | HITESH HARISHCHANDRA SAWANT | DASSAULT SYSTEMES MUMBAI 3DS | 1,33,684 | 44,537 | 89,147 | 66.7% |
| 25041541 | SHARAD DAGADU SURVE | MCKINSEY & COMPANY MUM | 97,092 | 14,882 | 82,210 | 84.7% |
| 22090817 | SHASHI BHUSHAN RAJAK | DASSAULT SYSTEMES GURUGRAM | 1,52,135 | 75,400 | 76,735 | 50.4% |
| 25041535 | ARUN RAMJI PAWAR | MCKINSEY & COMPANY MUM | 89,708 | 14,882 | 74,826 | 83.4% |

McKinsey (MUM/Gurgaon), Dassault Systemes, Hyatt and Apollo India sites dominate the top of the list.

## Output files (Google Drive → `SALARY FOLDER 2025-26/M13_FINAL_EXTRACTED`)

Per month (Dec/Jan/Feb/Mar):
- `<Month>_V2_50pct_CTC_ALL.csv` — every employee row with all computed columns (~2.5 MB each)
- `<Month>_V2_50pct_CTC_VIOLATIONS.csv` — violating rows only (~2.8–3.2k rows each)
- `<Month>_V2_50pct_CTC_SUMMARY.json` — month totals + top-10 by DIFF

## How it was produced (rerunnable)

The V2 workbooks (30–35 MB) exceed both the Drive-connector 10 MB download cap and the
n8n instance's binary memory limit, so the pipeline works fully server-side per month
(n8n workflows in the user's instance, Drive credential "Google Drive account 7"):

1. Drive API `files.copy` with `mimeType=application/vnd.google-apps.spreadsheet` → temp native Sheet (conversion happens on Google's side).
2. Sheets API: read rows 1–5 of the first tab to locate the header row (row 2 — the tab has 2 frozen rows), then `values:batchGet` (majorDimension=COLUMNS, UNFORMATTED_VALUE) for just the 10 needed columns.
3. One Code node computes all rule columns and builds the two CSVs + summary JSON as binaries (single item — avoids the ~20k-item memory blowup that crashes the instance).
4. Upload the three files to the Drive folder, delete the temp Sheet.

n8n workflows: `Jan/Feb/Mar V2 50pct CTC (Sheets API lean)` (IDs `NdeHjwbfpLr00pKj`, `RrO0OOu10Adpi7tC`, `NtATby7YGepjDDE5`), `Dec V2 50pct CTC (Sheets API)` + `Dec V2 50pct summary` (`hb9CXjLpsHuq0F5j`, `fD5YPztZRRHDGVh3`). To redo a month, run the workflow again (same filenames are re-uploaded as new Drive files).

## Notes / caveats

- Basis follows the user's instruction and the earlier `WageCode_50pct_vs_Consol_Discrepancy_Report.xlsx` convention: **FIXED_BASIC + FIXED_DA vs the sheet's `CTC` column**. The July "v2 method" pack (`Dec25_Mar26_WAGECODE_50PCT_PACK_v2.xlsx`) instead tested against FAQ-adjusted *remuneration*, which clears many rows — so its "persistent failer" counts are much lower than these raw CTC-basis counts. Both views are legitimate; this run is the raw CTC-basis employee-wise list that was asked for.
- `VIOLATION_DIFF_AMOUNT` = full allowance component (CTC minus basic+DA) on violating rows; `EXCESS_ABOVE_50PCT_OF_CTC` = the restructuring gap (how much basic+DA must rise, at constant CTC, to reach 50%). Month restructuring cost ≈ Σ excess ≈ ₹1.6–1.8 Cr/month on this basis.
