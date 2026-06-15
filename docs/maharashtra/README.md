# Maharashtra Trial Balance 24-25 — Grouped, with depreciation per schedule

Source: Google Drive folder **MAHARASHTRA ASSSIS DATA 24-25**
- Input: `Maharashtra Trial Balance With Header FY 24-25.xlsx`
- Grouping logic reused from: `Trial Balance 24-25_Maharashtra_GROUPED`

## What was done
1. **Grouping** applied to every file-level GL (same Pan-India line items + P&L/BS heads as the earlier grouped sheet).
2. **Reversed** the depreciation of **Rs 47,525.42** that had been booked against `ASSETS-COMPUTER` in the trial balance.
3. **Depreciation booked as per the attached schedule** (WDV method):
   | Head | Op WDV | Addition | Depreciation | Closing WDV |
   |---|---|---|---|---|
   | Computer | 373,713.67 | 118,123.00 | 448,320.16 | 43,516.51 |
   | Office Equipment | 93,289.55 | – | 42,045.60 | 51,243.95 |
   | Plant & Machinery | 6,212,537.74 | 1,753,900.00 | 1,441,925.23 | 6,524,512.51 |
   | Building | 13,801,575.42 | – | 672,136.72 | 13,129,438.70 |
   | **Total depreciation** | | | **2,604,427.71** | |
4. **Building** was not present in the Maharashtra TB; per instruction it was brought into the
   branch books (closing WDV 13,129,438.70) with the contra to the **Head Office / Inter-Unit account**,
   and its depreciation of 672,136.72 charged to P&L.

The restated grouped trial balance ties exactly: **Dr = Cr = 614,440,817.41**.

## Output
`Maharashtra_Trial_Balance_GROUPED_Dep_per_Schedule_FY24-25.xlsx` (4 tabs:
Grouped TB (Restated), Depreciation Schedule, Reconciliation, Summary by Head).
A copy was also uploaded to the Drive folder as
"Maharashtra Trial Balance 24-25 GROUPED (Dep per Schedule).xlsx".
