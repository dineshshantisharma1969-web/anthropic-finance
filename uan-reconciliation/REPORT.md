# UAN Reconciliation — Salary sheet ↔ PF ECR (FY2025-26)

Fill each monthly salary sheet's `UAN NO` column where it is blank, using the UAN
that was actually filed in that month's PF ECR, matched on employee code.

## Join key

`EMPCODE` (salary sheet) = `EMP CODE` (PF ECR). Both are the 8-digit ISPL employee
code. The ECR's `UAN NO` column is the source of truth. Existing salary UANs are
never overwritten — only blank cells are filled.

## Source files (Google Drive)

| Month | Salary sheet (AUDITOR REPLY folder) | PF ECR source | ECR sheet(s) / header row |
|-------|-------------------------------------|---------------|---------------------------|
| June  | `June_FY2526_LIVE_CHECK.xlsx`            | `FORMAT-JUNE_2026.xlsx`          | `Sheet1`, header row 5 |
| July  | `July_FY2526_SALARY_CORRECTED_10544.xlsx`| `ECR_PF_JULY2026_MERGED.xlsx`   | `Merged`, header row 1 |
| Aug   | (August salary sheet)                    | `ECR_PF_AUGUST2026_BUILD.xlsx`  | `AUG_DELHI` + `AUG_DMART` + `AUG_STEAGE` |

## Result (EMPCODE → UAN lookup)

| Month | ECR filed rows | Unique EMPCODE→UAN | Blank/no-UAN (excluded) | Conflicts | UAN length |
|-------|----------------|--------------------|-------------------------|-----------|------------|
| June  | 19,146 | 19,146 | 0 | 0 | all 12-digit |
| July  | 19,118 | 19,118 | 0 | 0 | all 12-digit |
| Aug   | 19,124 | 17,578 | 1,546 new joiners (no UAN filed yet) | 0 | all 12-digit |

Every EMPCODE maps to exactly one 12-digit UAN — no duplicates, no conflicts.
August new joiners have no UAN in the ECR (not yet generated), so they cannot be filled.

## Deliverable

For each month, a `<Month>_2026_UAN_LOOKUP.xlsx` with:
- `UAN_LOOKUP` sheet: `EMPCODE, UAN NO, NAME, F/H NAME, PF NO` (EMPCODE/UAN stored as text)
- `HOW_TO_USE` sheet with the fill formula.

Apply in the salary sheet (fills only blank `UAN NO`, keeps existing values):

```
=IF(TRIM(<UAN NO cell>)<>"", <UAN NO cell>,
    IFERROR(VLOOKUP(TEXT(<EMPCODE cell>,"0"), UAN_LOOKUP!$A:$B, 2, FALSE), ""))
```

## Notes / scope

- The salary sheets are ~20 MB, above the Drive tool's 10 MB read/write cap, so the
  reconciliation is delivered as a lookup list to apply, rather than an in-place rewrite.
- June: `FORMAT-JUNE_2026.xlsx` is the raw filed PF ECR (used in place of the 7.5 MB
  `June_2026_PF_Employee_Share_Match.xlsx`, which exceeds the download cap; same underlying
  filed-ECR UAN data). Small DMART/STEAGE June groups (~99 employees) may not be included.
- No employee PII is committed to this repo — only the build scripts and these counts.
  The generated lookup workbooks are shared directly with the user.
