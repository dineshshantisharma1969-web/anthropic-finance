# Master source + PivotTable/slicers — build instructions (FY 2025-26)

Goal: one fast, refreshable analytical model over all 12 reconciled months — without the
282 MB bloat of the all-formulas merge. Two stages: (1) build a lean source table,
(2) pivot off the Excel Data Model with slicers.

## Stage 1 — build the lean source table

Run locally where the monthly files live (they are 9–22 MB, too big for the cloud):

```bash
cd "C:\Users\Dinesh Sharma\Desktop\FINAL COMPLETE SALARY DATA 25-26"
'/c/Users/Dinesh Sharma/AppData/Local/Python/bin/python.exe' salary_reconciliation\build_master_source.py "MONTHS" --out "Salary_Master_Source_FY2025-26.xlsx"
```

It reads the biggest sheet of each `MONTHS\*.xlsx`, drops footer/total rows, keeps ~20
analysis columns as **values only**, stamps `MONTH`, and writes one `SourceData` sheet.
Validated total: 235,069 rows, REVISED_NET = ₹2,93,29,71,946 (ties to Reconciled_Summary).

## Stage 2 — PivotTable on the Data Model + slicers

1. Open `Salary_Master_Source_FY2025-26.xlsx`, click any cell in `SourceData`.
2. **Insert → PivotTable** → New worksheet → tick **"Add this data to the Data Model"** → OK.
   (Data Model = fast slicers and a small file at 235k rows; a classic pivot cache bloats.)
3. Build the pivot, e.g.:
   - **Rows:** `SITESTATE` then `DESIGNATIONNAME`
   - **Columns:** `MONTH`
   - **Values:** Sum of `REVISED_GROSS`, `REVISED_PF`, `ECR_PF`, `REVISED_NET_PAYABLE`, and Count of `EMPCODE` (headcount)
4. **PivotTable Analyze → Insert Slicer** → tick `MONTH`, `SITESTATE`, `DESIGNATIONNAME`,
   `RULE_APPLIED`, `HIGH_EARNER_EXCEPTION`. (Insert a **Timeline** only if you add a real date.)
5. To make `MONTH` sort Apr→Mar (not alphabetical): File → Options → Advanced → Edit Custom
   Lists → add `April,May,June,July,August,September,October,November,December,January,February,March`;
   then right-click a MONTH label → Sort → More Sort Options → by that custom list.

## Refresh each loop cycle

After the scheduled loop rewrites a month, re-run Stage 1 (overwrites the source), then in
Excel hit **Data → Refresh All**. Pivots and slicers update in place.

### Alternative — skip Stage 1 with Power Query (auto-append the folder)
Data → Get Data → From File → **From Folder** → select `MONTHS` → Combine & Transform →
in the editor keep only the lean columns + add a `MONTH` column from `Source.Name` → Close & Load
**To… → Only Create Connection + Add to Data Model**. Then build the pivot as above. Refresh All
re-reads the folder, so new/updated months flow through automatically. Use this if the 12 files'
headers line up; if they differ (column counts vary 53–58), the Python source-builder is safer.
