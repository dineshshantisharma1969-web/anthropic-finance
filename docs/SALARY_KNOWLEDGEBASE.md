# 🧠 SALARY KNOWLEDGEBASE — ISPL (Impressions Services)

**The single entry point for all salary / PF / ESI reconciliation knowledge.**
Last updated: 2026-07-04 · Maintained on branch `claude/pf-salary-reconciliation-2026-1x7pmd`

> **How to use this file:** Start here. Every source file, verified number, methodology
> rule, known discrepancy and rerun procedure is indexed below. When a new month is
> reconciled or a discrepancy is resolved, update this file in the same commit.

---

## 1. What this covers

| Scope | Status |
|---|---|
| **FY2025-26** — 12 monthly payrolls, reconciled + M13 annual true-up | ✅ Closed & verified |
| **FY2026-27 April** — reconciled (M12/M15 final) | ✅ PF verified · ⚠️ action list open |
| ~19–21k employees/month, pan-India, multi-site | |

**The three Golden Rules (never violated):**
1. `Σ REVISED_PF = ECR_PF` — salary PF must equal EPFO-filed ECR, per employee.
2. `Σ REVISED_ESIC = Future-sheet ESIC` — per employee.
3. **NET PAYABLE NEVER CHANGES** — all differences absorbed via OTHER DEDUCTION / attendance allowance.

---

## 2. Verified anchor numbers

### FY2025-26 (full year, M13 FINAL)
| Anchor | ₹ |
|---|--:|
| Net Payable (sacrosanct, drift 0) | **2,93,29,71,946** |
| Reconciled PAN PF (= ECR filed, gap 0) | **29,06,52,769** |
| Back-office PF | 1,64,19,591 |
| Booked PF (PAN + back-office) | 30,70,72,360 |
| Tally EPF-Employee payable ledger | 29,67,46,845 |
| Future-basis ESI (statutory anchor) | 1,86,93,848 |
| Professional Tax | 84,33,198 |
| M13+CL/Bonus merged Gross | 4,65,25,22,768 |
| M13+CL merged Net Payable | 3,19,40,63,202 |
| Bonus / Leave encashment | 2,77,73,882 / 4,42,61,081 |

### April 2026 (M12/M15 FINAL — footed row-by-row from the full 21,152-row sheet)
| Anchor | ₹ |
|---|--:|
| REVISED_PF = ECR_PF (gap **0**, 21,152/21,152 rows exact) | **2,52,21,042** |
| NETPAYABLE = REVISED_NET (drift **0**) | **25,99,37,250** |
| GROSS AMT (original) / REVISED_GROSS | 30,72,93,356 / 35,71,24,660 |
| ESIC original / REVISED_ESIC / Future_ESI | 14,92,853 / 3,18,634 / 3,56,370 |
| PT | 7,23,250 |
| **EXCESS_SALARY on ACTION_NEEDED=Y rows** | **5,44,58,591** (4,974 rows) |
| Rule mix | PF_ANCHOR 18,389 · PF_SECONDARY 1,403 · ESI_ONLY 463 · NO_PF_NO_ESI 506 · SKIP_ZERO_BASIC 391 |
| Independent ECR source check | DELHI ECR EE sum 2,54,07,193 (18,535 emp) > anchor by ~0.74% — expected (ECR-only emp + min-cap) ✅ |

---

## 3. Where everything lives

### A. In this repo (`docs/pf-salary-reconciliation/`)
| File | What it is |
|---|---|
| `CHECKS_AND_BALANCES_FY2025-26.md` | Full-year checks report (7 PASS · 5 REVIEW · 0 FAIL) |
| `SUMMARY_FY2025-26.csv` · `M13_RULE_STATS_FY2025-26.csv` | Month-wise summary + M13 rule stats |
| `dashboard.html` | Interactive FY25-26 dashboard (self-contained, open in browser) |
| `reconciliation_data.json` · `build.py` | Data + reproducible builder |
| `april-2026/CHECKS_AND_BALANCES_April2026.md` | April-26 checks (5 PASS · 1 REVIEW) |
| `april-2026/dashboard_April2026.html` | April-26 dashboard |
| `april-2026/ACTION_NEEDED_April2026.csv` | **The 4,974 open action rows** (sorted by excess, with reasons) |
| `april-2026/SUMMARY_April2026.csv` + build scripts | Summary + builders |

### B. In Google Drive (dinesh@impressionsgroup.in)
| Folder / file | Drive ID | Contains |
|---|---|---|
| **SALARY DATA 2026-27** | `1JkGyC90rOMhTLAbd5LqutdzMz-FKD3Ae` | New-year source data |
| ├─ `apr26_FULL_monthly_sheet.xlsx` (18 MB) | `1xOpgAh3hCd3dvshzwa1_tlPqvtOkiFyu` | **April-26 salary sheet (reconciliation input)** |
| └─ **desktop salary folder** | `1hoJ1-t6zCeptcsHAnpdfSvYQlTC6Mu6p` | April-26 run folder |
| &nbsp;&nbsp;&nbsp;├─ `reconcile.py` | `1sXJeh3hvs_8A3dkiYNvmUAte3nbnZJkx` | **End-to-end pipeline script** |
| &nbsp;&nbsp;&nbsp;├─ `SKILL.md` (consolidated) | `1YJM8xuFa-dNBeqIyTPxwp9qFr19axX44` | Condensed methodology |
| &nbsp;&nbsp;&nbsp;├─ `run_april26.bat` | `1c_G9a3hjR19SHkIlfuNbr5Y1zdWaZnXE` | Exact April-26 run command |
| &nbsp;&nbsp;&nbsp;└─ ECR `FORMAT-APRIL_2026_{DELHI,STEAGE,DMART}.xlsx` + `ESIC_CONSOLIDATED_APR_2026.xlsx` + outputs | — | Inputs & `April26_Reconciliation_Report.xlsx` (20 MB) |
| **Skill & monthly reports FY25-26** | `128jnomIpp1-5BihTKFduCaq8Y48cJ8xY` | Master methodology |
| ├─ `PF_SALARY_RECONCILIATION_SKILL_v4.md` | `1UpkJxN_INfsJ49FmExiTEExyYMe0-bdZ` | **The full skill (86 KB) — canonical rules** |
| └─ `SKILL_PATCH_minimum_wage_floor.md` | `1Po1B6FbRk0srcYZb92yv19dqZHIvhpz7` | Min-wage floor patch |
| **ANNUAL SALARY SUMMARY SHEET 25-26** | `11wRKHwswXFa8rCYDRh0iAjvSPWymCn5P` | Year-end summaries |
| ├─ `Monthly_Salary_Summary_FY2025-26.xlsx` | `16SuPoDTuNUzknNEM9xNnk58BKAalJl0T` | Clean self-footing month-wise |
| ├─ `Salary_Pivot_M13_MONTHWISE.xlsx` | `1ojKS5NUy4SHzU9HAQnhgMKcY84lf9dSx` | ESI-as-per-Future basis pivot |
| ├─ `M13_SUMMARY_and_MERGED_CLBONUS.xlsx` | `1ymG5Bfb_lTgyHUqeG588j8ZNdWSVLrgO` | M13 + CL/Bonus merged |
| ├─ `PF_ESI_Audit_Report_FY25-26.xlsx` (20 MB) | `16-yZy4vFRefZDffsw1fNsi6p_kJvjjJw` | Per-row year audit |
| ├─ `Salary_as_per_Max_SA_consolidated_SUMMARY.xlsx` | `1QjNLeXFy3nxn7P9V5FkRdoQv5MCuc26l` | **Tally books ledger totals** |
| └─ `v3_projection_addendum_for_skill.md` | `10i5y99PyuXPPMhSAXk-bK_Erd4cA4-Ij` | Projection-column corrections |
| **CORRECTED SALARY 25-26 (M13 FINAL)** | `1PU9QyY4VwyNrlHzwaBJj8Sku0qKmhmky` | 12 final monthly files + `FINAL_REPORT.md` (`1-7g0p1PoanRks_bOnXDWo7a2flf4h-Mm`) + `PF_M13_Exceptions_Review.xlsx` + `_change_logs/` |
| **MONTHLY SALARY FINAL DATA FOR 2025-26** | `1LiA13hSSNdDh3O0JsiANzCcDTGWONiS2` | Monthly final data |
| **ECR PF 2025-26** | `1YsX0QjjOSRYrhkFDPrEl95oJBQN1Thsp` | Filed ECR files |
| `Salary_Master_With_Summary_CORRECTED_v2.xlsm` | `1zGtlj2NZM7zY56BMYlp0PCfYdmFZSCyC` | Salary master workbook |

Open any ID via: `https://drive.google.com/file/d/<ID>/view` (files) or `/drive/folders/<ID>` (folders).

### C. Local (user's PC, D: drive) — confirmed paths
| What | Path on PC |
|---|---|
| **April-26 run folder** ("desktop salary folder" — reconcile.py, run_april26.bat, inputs & outputs) | `D:\Desktop Data\21062026\desktop salary folder` |
| **FY2025-26 canonical data folder** (all latest 25-26 salary data — the folder Dinesh works from) | `D:\Desktop Data\salary 25-26\CORRECTED SALARY 25-26 (M13 FINAL)_20260626_020401 (1)\CORRECTED SALARY 25-26 (M13 FINAL)_20260626_020401\ESI_WASHING_REALLOCATED` |

Find them again anytime: `dir /s /b D:\reconcile.py` (April run folder) · `dir /s /b "D:\Desktop Data\salary 25-26"` (2025-26 tree).
Open the 2025-26 folder instantly: `explorer "D:\Desktop Data\salary 25-26\CORRECTED SALARY 25-26 (M13 FINAL)_20260626_020401 (1)\CORRECTED SALARY 25-26 (M13 FINAL)_20260626_020401\ESI_WASHING_REALLOCATED"`

---

## 4. Methodology in one page

**Inputs:** salary sheet (header row 5) + one-or-more ECR files (dedup by EMP CODE within file, then sum EE across files) + Future reference sheet (tab `FR_sheet`, header row 3, ESI = col Q).

**PF rules:** Case B (ECR<PF & fixed B+DA ≤ 15000 → back-calc days) · Case A (ECR<PF & >15000 → park diff in OTHER_DED) · Cond 2 (ECR>PF → OTHER_DED goes down) · Not-in-ECR (BASIC=15001, PF=0). Multi-site: main PF row matches ECR; secondaries zeroed.

**Post-passes:** 12% basic fix → min-wage floor → enforce PF=12%(B+DA) (reduce days if needed) → integer days. **ESI passes E1–E4** (primary-site alignment, unmatched cleanup, PF/ESI ceilings, negative-OD shift, GF balancer). **Final:** projection cap, `ECR_PF_OUT = min(filed, REVISED_PF)`.

**M13 (annual true-up):** PF = 12% on BASIC+DA; ECR>0 → REVISED_BASIC = ECR/0.12 − DA (plug to attendance allowance); ECR=0 → project above ₹15,000 via day-reduction then basic lift. GROSS/PF/NET held.

**Validation set:** C1 OTHER_DED≥0 · C2 |NET drift|≤1 · C3 PF=12%±1 · C5 ATT_ALW≥0 · C7 GROSS foots · C9 days∈[1,31] · C10 ECR_capped≤REVISED_PF · C-MW basic≥floor.

**To rerun a month:**
```
python reconcile.py --salary <sheet>.xlsx --ecr <FORMAT-*.xlsx ...> \
  --future "<future sheet>.xlsx" --month YYYY-MM --salary-header 4 --out-prefix <Mon>YY
```
Run locally (files >10 MB exceed the Drive-connector download cap). To rebuild the repo summaries/dashboards: `python3 docs/pf-salary-reconciliation/build.py` (and `april-2026/build_apr26.py`).

---

## 5. Known discrepancies & open items

| # | Item | Status |
|---|---|---|
| 1 | **April-26: 4,974 ACTION_NEEDED rows, ₹5.45 Cr excess salary** — top reasons: paid above fixed rate (2,458), ESI-exempt but rate ≤ ₹21k (1,940), implied full-month ≫ rate (319), low attendance (257). List: `april-2026/ACTION_NEEDED_April2026.csv` | 🔴 **OPEN — needs decision** |
| 2 | April-26 ESI vs Future gap ₹37,736 (secondary-site / Future-only; expected per E1) — confirm in report's ESI_Audit tab | 🟡 Verify before ESI filing |
| 3 | FY25-26: `M13_SUMMARY` October net short ₹9,76,861 vs pivot (pre-final build) → **use pivot/monthly figure** | 🟡 Documented |
| 4 | FY25-26: `M13_SUMMARY` June PF short ₹858 → **use pivot/ECR figure** | 🟡 Documented |
| 5 | Jan-26/Feb-26 gross ≈ 2× other months (possible double/bonus run) — net ties; verify before statutory use | 🟡 Documented |
| 6 | M13+CL merged net vs Tally salary payable Δ ₹14,634 (~0.0005%) | 🟢 Immaterial |
| 7 | 2 M13 exceptions (DA alone > ECR/0.12; basic clamped) — in `PF_M13_Exceptions_Review.xlsx` | 🟢 Documented |

---

## 6. Glossary
**ECR** — Electronic Challan cum Return (EPFO filing; `EE` = employee PF). **Future sheet** — ESI reference ("ESI as per Future"). **M13** — 13th-month annual true-up rule. **Case A/B, Cond 2, Not-in-ECR** — the four PF adjustment rules. **PF_ANCHOR / PF_SECONDARY** — main vs secondary multi-site rows. **GC/GF/OD** — ADJ_WORKING_DAYS / REVISED_ATTENDANCE_ALLOWANCE / OTHER_DEDUCTION columns.

---

*Update discipline: every new month reconciled, discrepancy resolved, or file moved → update §2, §3, §5 here in the same commit. This file is the brain; keep it current.*
