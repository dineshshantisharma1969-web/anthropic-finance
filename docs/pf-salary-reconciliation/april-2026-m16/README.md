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
| In ECR, **absent from salary sheet** | 250 | 3,38,328 | **ACTION** — see `ECR-Only (250)` sheet |
| In salary, not in ECR | 966 | 0 | salary PF already ₹0 — nil effect |

The per-employee test is exact, not just aggregate: all 18,389 matched employees have
`ECR_PF = REVISED_PF` and `ECR_PF = PF as paid` within ₹1.

## ESI

| | ₹ |
|---|--:|
| ESIC as paid (col DR) | 14,92,853 |
| REVISED_ESIC (col GI) | 3,18,633.62 |
| Future_ESI (col GJ) | 3,56,369.62 |
| **Gap (Future − Revised)** | **37,736.00** |

Still **open** — same ₹37,736 flagged in `vault/40-Workings/2026-04-april-reconciliation.md`;
it has carried forward unresolved. By rule group: PF_SECONDARY 14,971 · SKIP_ZERO_BASIC 12,519 ·
PF_ANCHOR 10,213 · ESI_ONLY 33. Verify before the ESI filing.

## Net payable — Golden Rule 3

`NETPAYABLE` 25,99,37,250 = `REVISED_NET_PAYABLE` 25,99,37,250 → **drift ₹0** on all 21,152 rows.
The ~₹4.68 Cr of PF/basic movement is absorbed entirely through OTHER DEDUCTION
(2,48,71,379 → 7,16,47,734.60). Allowances untouched.

## Exceptions raised

1. **EMP 23040315 (AMIT, Haryana)** — EE ₹5,812 on ₹15,000 PF wages (expected ₹1,800). The only
   row across all three PF files where `EE ≠ 12% × PF WAGES`; also one of the 250 ECR-only
   employees. Likely arrears — confirm.
2. **4 rows where NET > GROSS** not explained by `REVISED_GROSS_NEW` (773 of the 777 such rows
   are explained — col DP is pre-restructure, col HH is the gross the net is paid from).
3. **5 employees with identical GROSS *and* NET on two rows** — possible duplicated rows rather
   than genuine multi-site.

## Note on the ₹15,000 ceiling

1,508 employees have PF wages **above** ₹15,000 (up to ₹75,400, EE up to ₹9,048; ₹8.90 lakh of
EE sits above the ₹1,800 ceiling). This ECR is filed on **actual wages, not capped**. That
matters for the Not-in-ECR rule, which sets BASIC = ₹15,001 to zero out PF on the assumption the
ceiling binds — it does not bind for these employees.

## Files

| File | What |
|---|---|
| `ISPL_April2026_PF_ESI_NetPayable_Reconciliation.xlsx` | 7 sheets: Summary · PF · ESI · Net Payable · ECR-Only (250) · Checks (13 PASS / 3 REVIEW) · Exceptions |
| `ECR_MERGED_April2026.csv` | merged per-employee ECR — 18,639 rows, EE 2,55,59,370 |
| `merge_ecr.py` | merges any `FORMAT*APRIL*2026*.xlsx` dropped beside it; auto-detects header row (STEAGE has a blank leading row), dedupes per file, ties each to its footer |
| `build_recon.py` | builds the workbook from `ECR_MERGED_April2026.csv` + `SALARY_extract.csv` |

`SALARY_extract.csv` (39 columns × 21,152 rows lifted from the 221-column salary sheet) is not
committed — regenerate it with the extract step in `build_recon.py`'s header comment.
