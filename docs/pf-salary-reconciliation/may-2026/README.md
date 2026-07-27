# May 2026 (FY2026-27) — PF / ESI / Net Payable reconciliation

Run date: 2026-07-27. Rules applied: `vault/20-Rules/` — [[pf-golden-rules]],
[[pf-ecr-case-rules]], [[pf-contribution-basis]], [[net-payable-sacrosanct]].

Same method as [`../april-2026-m16/`](../april-2026-m16/), against
**`May26_RECONCILED_FINAL_1.csv`** (21,800 rows). All three PF (ECR) files and all
seven ESI sources are merged from source rather than taking any salary-sheet column
as given.

## Before anything else — the extract ties to the sheet's own footer

| Footer control | Sheet | Extract |
|---|--:|--:|
| GROSS AMT | 31,04,80,069 | 31,04,80,069 |
| PF | 2,79,77,383 | 2,79,77,383 |
| ESIC | 15,29,658 | 15,29,658 |
| TOTAL DEDUCTION | 3,55,86,168 | 3,55,86,168 |
| NET PAYABLE | 27,48,93,901 | 27,48,93,901 |

Getting here required a correction. **137 rows carry a name, a gross and a net but no
employee code** — ₹4,18,888, all at *MINISTRY OF RAILWAY_HISAR & BIKANER OBHS*, paid in
full with zero attendance days and zero deductions of any kind. A first pass filtered on
EMPCODE and silently dropped them, which left gross and net ₹4,18,888 short of the
sheet's own footer. They are now carried through and listed on their own sheet. They
cannot be matched to PF or ESI, because there is nothing to match on.

## PF — the May position is *not* April's

In April the ECR tied to PF **as paid**. In May it ties to **REVISED_PF**: the salary
sheet deducted ₹2,79,77,383 of PF but only ₹2,63,78,587 was filed. So the match is
merged ECR vs REVISED_PF, and the paid-vs-filed movement is a separate bridge.

### Step 1 — merge the PF (ECR) files

| File | Employees | EE PF ₹ | Net challan ₹ |
|---|--:|--:|--:|
| DELHI (pan-India, 38 locations) | 18,758 | 2,65,83,517 | 5,53,39,028.09 |
| DMART | 68 | 88,529 | 1,84,418.13 |
| STEAGE | 35 | 57,559 | 1,19,883.58 |
| **MERGED ECR** | **18,861** | **2,67,29,605** | **5,56,43,329.80** |

0 duplicate `EMP CODE` rows in any file; no employee appears in more than one file.
Each file's EE ties to its own footer, and all three challans rebuild to the rupee as
`EE + ER DIFF + EPS + 0.5%×PF wages (admin) + 0.5%×EPS wages (EDLI)`.

### Step 2 — which salary column is the ECR?

The sheet carries **two** ECR columns that disagree. The merge settles it:

| | ₹ | vs merged ECR | Verdict |
|---|--:|--:|---|
| Merged ECR (actual) | 2,67,29,605 | — | the benchmark |
| col `ECR_PF` (= REVISED_PF) | 2,63,78,587 | −3,51,018 | **correct basis** |
| col `ECR pf` | 2,90,27,137 | **+22,97,532** | **wrong — do not use** |

### Step 3 — bridge merged ECR to REVISED_PF

Gap **₹3,51,018**, explained to the rupee:

| Bucket | Employees | ₹ | Treatment |
|---|--:|--:|---|
| ECR-only, **BACK OFFICE** | 194 | 3,24,740 | **EXPLAINED** — separate payroll, never on the site sheet |
| ECR-only, at **named client sites** | 52 | 24,894 | **OPEN** — should have been on the salary sheet |
| matched, ECR ≠ REVISED_PF | 1 | 1,384 | EMP 26040419 — see Exceptions |

Every other one of the 18,615 matched employees has `ECR = REVISED_PF` within ₹1.

### Step 4 — the restructure movement

| | ₹ |
|---|--:|
| PF deducted from staff | 2,79,77,383 |
| REVISED_PF (actually filed) | 2,63,78,587 |
| **Movement** | **−15,98,796** |
| — 1,894 matched employees whose PF changed | −9,32,828 |
| — 1,061 employees not in the ECR at all | −6,65,968 |

Staff were over-deducted before the restructure. Net pay is unaffected — the whole
movement is absorbed through OTHER DEDUCTION.

## ESI

### Step 1 — merge the seven sources

| Source | Employees | ESI employee ₹ | Covers |
|---|--:|--:|---|
| ESIC REGISTER | 2,869 | 3,17,297.00 | Mumbai, Hyderabad, Bangalore, Pune, Ahmedabad, Chennai, Vizag, Nagpur, Aurangabad, Dehradun, Indore |
| FUTURE (`FR_sheet (2)`) | 9,433 | 9,45,246.00 | Future-managed population |
| KOLKATA | 2,458 | 2,24,259.00 | West Bengal |
| GUWAHATI | 619 | 36,063.00 | Assam |
| ODISHA | 220 | 22,613.00 | Odisha |
| JAMSHEDPUR | 49 | 4,897.00 | Jharkhand |
| PATNA | 46 | 3,320.52 | Bihar |
| rows read | 15,694 | 15,53,695.52 | |
| **MERGED ESI** | **15,687** | **15,53,695.52** | 7 employees appear on more than one row |

**Independent control:** the register's own `Challan Details` sheet gives 2,869 employees
and ₹3,17,297 — the merge reads exactly that. Its ₹413 difference against the challans
actually paid is Dehradun ₹249 + Indore ₹122 (no challan raised) plus ₹42 of per-location
rounding — fully explained.

No exact duplicate rows this month. As in April, the regional files legitimately repeat an
EMPCODE across day-blocks; those rows are **summed**, never deduped. Only 3 employees
appear in two different sources, confirming the sources cover complementary populations.

May's Future workbook contains only `FR_sheet (2)` — which settles the sheet-name
ambiguity flagged in April.

### Step 2 — match to the salary sheet

| | Employees | ₹ |
|---|--:|--:|
| ESI actually filed (merged) | 15,687 | 15,53,695.52 |
| ESIC deducted in salary | 15,870 | 15,29,658.00 |
| **Gap (filed − deducted)** | | **24,037.52** |

Four buckets, netting exactly to the gap:

| Bucket | Employees | ₹ | Meaning |
|---|--:|--:|---|
| **A** — deducted in salary, **not filed anywhere** | 427 | −32,108.00 | file it, or refund the employee |
| — of which on a **not-paid list** | 118 | −9,049.00 | filing exists; only payment is outstanding |
| — remainder, genuinely unaccounted | 309 | −23,059.00 | **OPEN** |
| **B** — filed, employee **not on the salary sheet** | 231 | +11,682.00 | FUTURE 219 · KOLKATA 10 · REGISTER 2 |
| **C** — filed **more** than deducted | 4,068 | +95,245.00 | employee under-deducted |
| **D** — deducted **more** than filed | 1,733 | −50,781.48 | over-deducted, or a filing missing |
| match exactly (not listed) | 9,655 | 0 | nothing to do |

Bucket A is materially smaller than it first looks: the Future workbook carries its **own**
`Not Paid` sheet (67 employees) alongside the register's (56). April's script only read the
register's. Folding both in moves 118 employees and ₹9,049 out of "never filed" and into
"filed, payment pending" — a different action entirely.

### Salary-sheet ESI columns

`REVISED_ESIC` = `ESIC AS PER FUTURE` = ₹9,35,122 on **every row**. May has no `Future_ESI`
column, so **April's ₹37,736 Future-vs-Revised gap has no May equivalent** — nothing open here.

## Net payable — Golden Rule 3

`NETPAYABLE` 27,48,93,901 = `REVISED_NET_PAYABLE` 27,48,93,901 → **drift ₹0** on all
21,800 rows. Gross moves +₹3,55,54,218 and total deduction moves by exactly the same
amount, absorbed through OTHER DEDUCTION (7,81,665 → 3,85,29,218).

`GROSS − TOTAL DEDUCTION = NET` holds on every row on both the original and the revised
side. Note that TOTAL DEDUCTION is *not* just PF+ESIC+PT+LWF+OTHER DEDUCTION — it also
carries advances, TDS, food, insurance and welfare recoveries (₹44.60 lakh). Those are
untouched by the restructure bar ₹1 of rounding on each of 3 rows.

## Exceptions raised

1. **52 ECR-only employees at named client sites — ₹24,894.** Not back office, so the
   omission from the salary sheet is unexplained. (April: 63 / ₹25,669 — the same issue,
   slightly smaller.)
2. **137 salary rows with no employee code — ₹4,18,888**, all at one site. Cannot be
   reconciled to PF or ESI. Get the codes allotted, then re-run for that site.
3. **309 employees, ₹23,059** — ESIC deducted but no ESI filed and not on any not-paid list.
4. **231 employees, ₹11,682** — ESI filed for staff who never appear on the salary sheet.
5. **EMP 26040419 (DIPANKAR MONDAL)** — ECR filed ₹1,384 against a row with basic ₹0
   (rule `SKIP_ZERO_BASIC`). PF filed for a zero-basic row.
6. **EMP 23040315 (AMIT)** — EE ₹5,812 on ₹15,000 PF wages (12% = ₹1,800). The only row in
   any PF file where `EE ≠ 12% × PF WAGES`. **Recurs from April** — looks like arrears; confirm.
7. **10 employees with identical GROSS *and* NET on two rows** — possible duplicated rows
   rather than genuine multi-site. (April: 5.)

## Note on the ₹15,000 ceiling

1,713 employees have PF wages **above** ₹15,000; ₹9,35,943 of EE sits above the ₹1,800 cap.
This ECR is filed on **actual wages, not capped**, which matters for the Not-in-ECR rule —
that rule sets BASIC = ₹15,001 to zero out PF on the assumption the ceiling binds. It does
not bind for these employees.

## Files

| File | What |
|---|---|
| `ISPL_May2026_PF_ESI_NetPayable_Reconciliation.xlsx` | 13 sheets: Summary · **Detail (all 21,800 rows)** · PF Reconciliation · ESI Merge & Match · ESI Diff — summary · ESI Diff (emp-wise) · ESI Not-Paid (123) · ESI — salary cols only · Net Payable · ECR-Only (246) · **No EmpCode Rows (137)** · Checks (26 PASS / 8 REVIEW) · Exceptions |
| `ECR_MERGED_May2026.csv` | merged per-employee ECR — 18,861 rows, EE 2,67,29,605, with `SITE_NAME` / `LOCATION` / `IS_BACK_OFFICE` |
| `ESI_MERGED_May2026.csv` | merged per-employee ESI — 15,687 rows, ₹15,53,695.52 |
| `ESI_SOURCE_SUMMARY_May.csv` | per-source ESI figures, so no total is hardcoded downstream |
| `ESI_NOTPAID_May2026.csv` | 123 filed-but-unpaid employees (56 register + 67 Future) |
| `extract_salary.py` | lifts 38 columns out of the 218-column sheet; keeps the no-EMPCODE rows so totals tie to the footer |
| `merge_ecr.py` | merges the three PF files; auto-detects header row, dedupes per file, ties each to its footer |
| `merge_esi.py` | merges the seven ESI sources; sums day-split rows, reads both not-paid sheets |
| `build_recon_may.py` | builds the workbook from the merged CSVs + `SALARY_extract.csv` |

`SALARY_extract.csv` is not committed — regenerate it by running `extract_salary.py` beside
`May26_RECONCILED_FINAL_1.csv`.

**`Detail (all rows)`** is the main working sheet: one row per salary row, 28 columns, frozen
panes + autofilter, totals strip pinned at row 1. The merged ECR and merged ESI are attributed
to each employee's anchor row (the one carrying REVISED_PF), so the gap columns read true per
employee instead of double-counting across multi-site rows.
