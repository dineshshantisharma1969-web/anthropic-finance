# PF / ESI Salary Reconciliation — Checks & Balances
## ISPL · May-2025 (M13 FINAL) · Full row-level audit

> **Scope:** `May_M13_FINAL.xlsx` (Drive `1xUX0E1GSEV7RUED7eS60rhNP4DVLiNMf`, sheet *Salary (Corrected)*, **19,327 employee rows** + 5 footer rows, 264 columns) audited row-by-row against the `pf-salary-reconciliation` skill (`PF_SALARY_RECONCILIATION_SKILL_v4.md`), **with emphasis on the recently added checks**: Rule M6/C10-hard (v4.1 addendum), the C9–C13 day-adjustment set, the C-MW minimum-wage floor, the v3 projection addendum (2026-06-21), and the M17+M18a–e row-level worklist checks (2026-07-04).
>
> The 21 MB source exceeds the 10 MB Drive-connector cap; it was fetched **in full** via 5 ranged binary slices (n8n workflow *May M13 FINAL - ranged slice bridge*) and reassembled byte-exact (22,042,972 bytes). This is a **100 % row-coverage** audit, not an aggregate-level one.

**Result: 19 PASS · 8 REVIEW · 1 FAIL (28 checks).**
All three Golden Rules hold exactly. The one FAIL is **Rule M6** (3,310 rows whose day count doesn't justify the PF wage — fixable by the skill's Step-6 day adjustment). Every other flag is a review/structural item, quantified below.

---

## 1. Verified anchors (hard gate before any check ran)

| Anchor | ₹ | Ties to |
|---|--:|---|
| NETPAYABLE = REVISED_NET_PAYABLE (drift **0**) | **23,21,02,234** | SUMMARY_May2025 / FY checks report |
| Σ REVISED_PF = Σ ECR_PF (gap **0**, per-employee 0 across 17,681 employees) | **2,29,77,657** | SUMMARY_May2025 |
| Booked PF (original column) | 2,46,10,756 | FY report May row |
| Original ESIC | 15,05,739 | FY report May row |
| REVISED_ESIC (`ESIC.1`) vs ESIC-as-per-Future | 14,66,653 vs 14,66,656.53 (Δ ₹3.53) | Future register |
| BASIC + DA (original) | 20,98,29,942 | FY report May row |

## 2. Golden Rules

| Rule | Status | Detail |
|---|---|---|
| G1 — Σ REVISED_PF = ECR_PF per employee | ✅ PASS | 0 employees with gap > ₹1; total gap ₹0 |
| G2 — Σ REVISED_ESIC = Future-sheet ESIC | ✅ PASS | Per-employee gap 0 for all 14,976 matched employees (max ₹0.49); total Δ ₹3.53 rounding |
| G3 — NET PAYABLE unchanged | ✅ PASS | 0 rows with |REVISED_NET − NETPAYABLE| > ₹1; total drift ₹0.00 |

## 3. Post-reconciliation integrity set (C1–C8)

| Check | Status | Detail |
|---|---|---|
| C1 `OTHER_DEDUCTION ≥ 0` | ✅ PASS | 0 violations |
| C2 `NET = GROSS − TOTAL_DED` (±1) | ✅ PASS | 0 violations (max |diff| ₹0.34) |
| C3 `REVISED_PF = 12%×(B+DA)` (±1, PF>0) | ✅ PASS | 0 violations on 16,688 PF rows |
| C4 `ESIC.1 = 0.75%×GROSS_NEW(final)` | ℹ️ INFO | **Strict on all 14,976 ESI rows**, 0 relaxed |
| C5 `REVISED_ATT_ALLOWANCE ≥ 0` | ✅ PASS | 0 violations |
| C6 `REVISED_TOTAL_DED ≥ 0` | ✅ PASS | 0 violations |
| C7 `GROSS = B+DA+ATT` (±1) | ✅ PASS | 0 violations |
| C8 `REVISED_NET = NETPAYABLE` (±1) | ✅ PASS | 0 violations |

## 4. Recently added checks (the focus of this audit)

### 4a. Day-adjustment / ceiling set C9–C13 + Rule M6 (v4.1 addendum)

| Check | Status | Detail |
|---|---|---|
| C9 `ADJ_WORKING_DAYS ∈ [1,31]` | ✅ PASS | 0 violations on active rows (553 SKIP_ZERO_BASIC rows excluded by design) |
| C-INT days integer | ⚠️ REVIEW | **468 rows** carry fractional day counts (day-tinker residue) — cosmetic; round on next rebuild |
| C10 `PF>0 ⇒ B+DA ≤ 15,001` | ⚠️ REVIEW | **1,499 rows** — every one has **ECR filed above the ₹1,800 EE cap**, so basic back-solved > ₹15k by construction. PF = ECR held (Golden Rule 1 wins). Structural, mirrors the Maharashtra above-cap finding; cannot satisfy the ceiling without breaking G1 |
| **M6 / C10-hard** `ECR_PF>0 ⇒ (B+DA)×31/ADJ ≤ 15,000.5` | ❌ **FAIL** | **3,310 rows** (beyond the 1,499 structural above) project above ₹15k purely because ADJ_DAYS is too low (median projection ₹16,034, p99 ₹24,417). **Fixable per the skill: send back through Step 6 — `ADJ_DAYS = ceil((B+DA)×31/15000)`; feasible (≤ 31) for all 3,310 rows.** Example: EMPCODE 23051955, B+D 15,000, ADJ 27 → proj ₹17,222; set ADJ = 31 → proj ₹15,000 ✓ |
| C11 `PF=0 ⇒ BD projection > 15K` | ✅ PASS | 0 violations |
| C12 `ESI>0 ⇒ GROSS ≤ 21,001` | ⚠️ REVIEW | **672 rows** — all are **exactly 0.75%×gross and tie to the Future register**: ESI contribution-period continuation (employee stays contributory till period end even when gross crosses ₹21k). Statutory behaviour, not book errors |
| C13 `ESI=0 ⇒ gross projection > 21K` | ✅ PASS | 0 violations |
| ECR cap `ECR_PF ≤ REVISED_PF` | ✅ PASS | 0 violations |

### 4b. C-MW minimum-wage floor

| Check | Status | Detail |
|---|---|---|
| C-MW `REVISED_BASIC ≥ (BASIC/NORMALDAYS)×ADJ_DAYS` | ⚠️ REVIEW | **6,800 of 16,688 PF rows** sit below the original-rate floor because M13 back-solves basic from ECR (`ECR/0.12 − DA`, remark `BACKSOLVED_TO_BENCHMARK`). Composition: **1,290** are the ₹15k ceiling clamp (min-wage basic > PF ceiling — floor can never hold with PF at ₹1,800); **5,510** others (median shortfall ₹102, p90 ₹6,014). **6,374 of 6,800 still pay ≥ the floor at GROSS level** via attendance allowance, so actual pay honours minimum wage; the shortfall is in the *basic head* labelling only. Known M13-design tension: the skill's MW-floor rule (lift basic, cap ECR) vs the M13 rule (pin basic to ECR benchmark). Decide once and apply to all 12 months |

### 4c. v3 projection addendum (2026-06-21)

| Check | Status | Detail |
|---|---|---|
| Stored vs recomputed projections | ℹ️ INFO | 12,377 rows drift > ₹5 — the addendum's documented limitation (stored values computed mid-pipeline). All checks here use recomputed `RGN(final)×31/ADJ` |
| IMPLAUSIBLE_PROJECTION (> ₹1,00,000) | ⚠️ REVIEW | **199 rows** balloon on low ADJ days — the flag population the column was built for |

### 4d. M17 + M18a–e row-level worklist (2026-07-04) — recomputed from scratch

| Workstream | This audit | Existing `May25_WORKLIST` | Match |
|---|---|---|---|
| Recovery review rows | 3,713 (pool ₹94,43,240) | 3,713 (97 HIGH ₹10,87,266 + ₹83,55,974) | ✅ exact |
| — HIGH (> ₹10k, cash-capped) | 97 rows ₹10,87,266 | 97 rows ₹10,87,266 | ✅ exact |
| — cleared by M18 tolerance | 15,061 of 18,774 scanned | 15,061 | ✅ exact |
| ESI enrollment needed (M18c) | 350 employees, ₹2,10,745/mo exposure | 350, ₹2,10,745 | ✅ exact |
| Wage Code 50% fails | 1,097 rows, shortfall ₹28,80,664/mo | 1,097, ₹28,80,664 | ✅ exact (65 rows < 30 % incl. 62 structural + 3 OT/low-day-noted) |

### 4e. ESI block invariants

| Check | Status | Detail |
|---|---|---|
| Multi-site secondary rows ESI = 0 | ✅ PASS | 0 employees with ESI on more than one row |
| Per-employee ESI = Future | ✅ PASS | 14,976 matched employees, 0 gaps (uses `ESIC AS PER FUTURE`; the older `FUT_ESIC` column is stale — total ₹9,92,143 — do not reconcile against it) |

## 5. Action list

| # | Item | Owner call |
|---|---|---|
| 1 | **M6 FAIL — 3,310 rows**: rerun Step-6 day adjustment (`ADJ_DAYS = ceil((B+DA)×31/15000)`, all feasible ≤ 31) before treating May M13 as filing-grade | 🔴 fix in sheet |
| 2 | C-MW policy: choose MW-floor-wins (lift basic, cap ECR at revised) or M13 ECR-benchmark (current) — apply uniformly across all 12 months; only 426 rows fall below floor at gross level | 🟡 decide |
| 3 | 468 fractional ADJ_WORKING_DAYS → round to integers on next rebuild | 🟡 cosmetic |
| 4 | 97 HIGH recovery rows (₹10.87 L) → verify/decide in `May25_WORKLIST_Recovery_ESI_WageCode.xlsx` | 🟡 open (pre-existing) |
| 5 | 350 ESI enrollment + 1,097 wage-code rows → pre-existing worklists stand, re-confirmed | 🟡 open (pre-existing) |
| 6 | 1,499 above-cap ECR rows + 672 ESI period-continuation rows → documented statutory composition, no sheet change | 🟢 documented |

## 6. Reproduce

```
python3 may25_checks.py May_M13_FINAL.xlsx <out_dir>
```
Outputs `may25_check_results.json` + `May25_M13_check_violations.xlsx` (one tab per flagged check, incl. the 3,310 M6 rows). Source fetched via the n8n *ranged slice bridge* workflow (5 × ~4.4 MB parts `May_M13_FINAL.part1of5.bin`…`part5of5.bin` in the *ISPL SALARY AUDIT 25-26* Drive folder — safe to delete after use).

---
*Audited 2026-07-16 against PF_SALARY_RECONCILIATION_SKILL_v4.md (+v4.1 M6 addendum, v3 projection addendum 2026-06-21, M17/M18 worklist checks 2026-07-04).*
