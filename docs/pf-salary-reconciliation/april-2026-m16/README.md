# April 2026 (FY2026-27) — PF / ESI / Net Payable reconciliation (M16 basis)

Run date: 2026-07-27. Rules applied: `vault/20-Rules/` — [[pf-golden-rules]],
[[pf-ecr-case-rules]], [[pf-contribution-basis]], [[net-payable-sacrosanct]].

Supersedes nothing: the earlier `../april-2026/` folder is the 2026-06-19 run against
`April26_Reconciliation_Report.xlsx`. This run is against
**`April26_RECONCILED_FINAL_M16_PATCHED.xlsx`** (21,152 rows) and, unlike the earlier run,
merges **all three** PF (ECR) files rather than taking the sheet's `ECR_PF` column as given.

## Step 1 — merge the PF (ECR) files

| File | Employees | EE PF ₹ | Net challan ₹ |
|---|--:|--:|--:|
| DELHI (pan-India, 41 locations) | 18,535 | 2,54,07,193 | 5,28,90,387.72 |
| DMART | 69 | 98,717 | 2,05,648.40 |
| STEAGE | 35 | 53,460 | 1,11,357.15 |
| **MERGED ECR** | **18,639** | **2,55,59,370** | **5,32,07,393.28** |

- **0 duplicate `EMP CODE` rows** in any file, and **no employee appears in more than one
  file** — so the cross-file sum is clean. (The skill's duplicate-row trap did not bite here,
  but `merge_ecr.py` still dedupes per file before summing.)
- Each file's EE total ties to its own footer row; DELHI's net challan rebuilds exactly as
  `EE + ER DIFF + EPS + 0.5%×PF wages (admin) + 0.5%×EPS wages (EDLI)`.

## Step 2 — match to the April salary sheet

| | ₹ |
|---|--:|
| Merged ECR | 2,55,59,370 |
| Salary sheet PF (col DQ, as paid) | 2,52,21,042 |
| **Gap** | **3,38,328** |

Gap is **fully explained**, to the rupee:

| Bucket | Employees | ₹ | Treatment |
|---|--:|--:|---|
| Matched — ECR = salary PF | 18,389 | 2,52,21,042 | no adjustment; **per-employee gap ₹0** |
| In ECR, **absent from salary sheet** | 250 | 3,38,328 | split below |
| — of which **BACK OFFICE** staff | 187 | 3,12,659 | **EXPLAINED** — back office is on a separate payroll, so never appears on the site-based salary sheet (confirmed by client 2026-07-27; the ECR's own `Site name` column labels them `BACK OFFICE <state>`) |
| — of which at **named client sites** | 63 | 25,669 | **OPEN** — these sit at real client sites (Kamakhya, Bikaner OBHS, DLF Magnolias, Accenture, Adobe …) and should have been on the salary sheet |
| In salary, not in ECR | 966 | 0 | salary PF already ₹0 — nil effect |

The per-employee test is exact, not just aggregate: all 18,389 matched employees have
`ECR_PF = REVISED_PF` and `ECR_PF = PF as paid` within ₹1.

## ESI

### Step 1 — merge the ESI folder

Seven sources. They cover **different populations**, so the sum is additive, not a
double count — the Future (FR) sheet and the in-house ESIC register overlap on exactly
**one** employee.

| Source | Employees | ESI employee ₹ | Covers |
|---|--:|--:|---|
| ESIC REGISTER (`ESIC` sheet) | 2,934 | 3,17,855.00 | Mumbai, Hyderabad, Bangalore, Pune, Ahmedabad, Chennai, Vizag, Nagpur, Aurangabad, Dehradun, Indore |
| FUTURE (`FR_sheet`) | 9,188 | 8,77,142.25 | Future-managed population |
| KOLKATA | 2,662 | 2,37,230.00 | West Bengal |
| GUWAHATI | 722 | 50,742.00 | Assam |
| ODISHA | 225 | 22,029.00 | Odisha |
| JAMSHEDPUR | 43 | 5,072.00 | Jharkhand |
| PATNA | 47 | 3,161.37 | Bihar |
| rows read | 15,821 | 15,13,231.62 | |
| less: 5 exact duplicate rows (all KOLKATA) | −5 | −33.01 | |
| **MERGED ESI** | **15,576** | **15,13,198.61** | |

Unlike the PF merge, the regional files legitimately carry the same EMPCODE on several
rows (a month split across day-blocks or sites) — 184 employees. Those are **summed**;
deduping them would understate ESI. Only exact duplicate rows are dropped.

The register's `NOT PAID` sheet (50 employees) is held aside — reasons are *left*,
*bank error*, *ESIC not generated*, *data not received*.

### Step 2 — match to the April salary sheet

| | Employees | ₹ |
|---|--:|--:|
| Merged ESI (filed) | 15,576 | 15,13,198.61 |
| Salary sheet ESIC (col DR, as paid) | 19,355 | 14,92,853.00 |
| **Gap (filed − paid)** | | **20,345.61** |

Bridge (ties exactly):

| Bucket | Employees | ₹ |
|---|--:|--:|
| Matched, filed ≠ paid | 15,260 | +43,929.61 |
| Filed but **not in the salary sheet** | 316 | +20,046.00 |
| In salary, ESIC deducted but **not filed** | 512 | −43,630.00 |
| **= Gap** | | **20,345.61** |

Filed-but-not-in-salary splits FUTURE 287 (₹17,396) · GUWAHATI 17 (₹1,039) ·
KOLKATA 10 (₹1,436) · REGISTER 2 (₹175).

### Salary-sheet ESI columns

| | ₹ |
|---|--:|
| ESIC as paid (col DR) | 14,92,853.00 |
| REVISED_ESIC (col GI) | 3,18,633.62 |
| ESIC AS PER FUTURE (col GK) | 3,18,633.62 |
| Future_ESI (col GJ) | 3,56,369.62 |
| **Future_ESI − REVISED_ESIC** | **37,736.00** |

`ESIC AS PER FUTURE` ties **exactly** to `REVISED_ESIC`, so the ₹37,736 is the
Future_ESI-vs-Revised item carried forward from the June run — still open.

**Employee-wise difference detail** is on the `ESI Diff (emp-wise)` sheet — 13,139
employees, one row each, with `ESIC paid` / `ESIC as per Future` / `DIFF DR−GK`,
`REVISED_ESIC` / `Future_ESI` / `DIFF GJ−GI`, and `merged filed ESI` / `DIFF filed−paid`.
Headline differences: **DR − GK = ₹11,74,219.38** across 12,613 employees (paid > Future
on 12,612 of them), **GJ − GI = ₹37,736**, **filed − paid = ₹20,345.61**.

## Net payable — Golden Rule 3

`NETPAYABLE` 25,99,37,250 = `REVISED_NET_PAYABLE` 25,99,37,250 → **drift ₹0** on all 21,152 rows.
The ~₹4.68 Cr of PF/basic movement is absorbed entirely through OTHER DEDUCTION
(2,48,71,379 → 7,16,47,734.60). Allowances untouched.

## Exceptions raised

1. **63 ECR-only employees at named client sites — ₹25,669.** Not back office (their ECR `Site name`
   is a real client site), so their omission from the salary sheet is unexplained. Mostly small
   part-month amounts (₹43–₹1,680), which points at joiners/leavers missed in the April run.
   Largest concentrations: Kamakhya MCC Depot (8, ₹8,786), Bikaner OBHS (4, ₹3,604),
   Kamakhya (4, ₹2,412), DLF Magnolias (6, ₹964).
2. **EMP 23040315 (AMIT)** — EE ₹5,812 on ₹15,000 PF wages (expected ₹1,800). The only row across
   all three PF files where `EE ≠ 12% × PF WAGES`. He is back office, so within the explained
   bucket, but the amount itself still looks like arrears — confirm.
3. **4 rows where NET > GROSS** not explained by `REVISED_GROSS_NEW` (773 of the 777 such rows
   are explained — col DP is pre-restructure, col HH is the gross the net is paid from).
4. **5 employees with identical GROSS *and* NET on two rows** — possible duplicated rows rather
   than genuine multi-site.

## Note on the ₹15,000 ceiling

1,508 employees have PF wages **above** ₹15,000 (up to ₹75,400, EE up to ₹9,048; ₹8.90 lakh of
EE sits above the ₹1,800 ceiling). This ECR is filed on **actual wages, not capped**. That
matters for the Not-in-ECR rule, which sets BASIC = ₹15,001 to zero out PF on the assumption the
ceiling binds — it does not bind for these employees.

## Files

| File | What |
|---|---|
| `ISPL_April2026_PF_ESI_NetPayable_Reconciliation.xlsx` | 11 sheets: Summary · **Detail (all 21,152 rows)** · PF · ESI · Net Payable · ECR-Only (250, split back-office vs client-site) · **ESI Merge & Match** · **ESI Diff (emp-wise)** · **ESI Not-Paid (50)** · Checks (17 PASS / 8 REVIEW) · Exceptions |

**`Detail (all rows)`** is the main working sheet — one row per salary row (21,152), 30 columns,
frozen panes + autofilter, with a totals strip pinned at row 1. Carries PF as paid, the merged
ECR PF, PF gap, REVISED_PF, the ESI trio (ESIC / REVISED_ESIC / FUTURE_ESI + gap), other
deduction before/after, gross before/after, net before/after, the rule applied, and whether the
employee matched the ECR. ECR PF is attributed to the employee's `PF_ANCHOR` row so the gap
column reads true per employee rather than double-counting across multi-site rows.
| `ECR_MERGED_April2026.csv` | merged per-employee ECR — 18,639 rows, EE 2,55,59,370, incl. `SITE_NAME` / `LOCATION` / `IS_BACK_OFFICE` |
| `merge_esi.py` | merges the 7-file ESI folder into `ESI_MERGED_April2026.csv`; sums day-split rows, drops only exact duplicates, emits `ESI_SOURCE_SUMMARY.csv` so no total is hardcoded downstream |
| `add_esi.py` | adds the three ESI sheets to the workbook |
| `merge_ecr.py` | merges any `FORMAT*APRIL*2026*.xlsx` dropped beside it; auto-detects header row (STEAGE has a blank leading row), dedupes per file, ties each to its footer |
| `build_recon.py` | builds the workbook from `ECR_MERGED_April2026.csv` + `SALARY_extract.csv` |

`SALARY_extract.csv` (39 columns × 21,152 rows lifted from the 221-column salary sheet) is not
committed — regenerate it with the extract step in `build_recon.py`'s header comment.
