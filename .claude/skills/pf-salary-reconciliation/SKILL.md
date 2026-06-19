---
name: pf-salary-reconciliation
description: >
  PF (Provident Fund) AND ESI reconciliation of a monthly pan-India salary sheet
  against ECR (Electronic Challan cum Return) data and an ESI "Future reference"
  sheet. Use whenever the user mentions PF reconciliation, ECR matching, salary PF
  adjustment, revised basic, "Case A/Case B/Cond 2/Not in ECR", ESI-as-per-future,
  Future reference sheet, adjusting ADJ_WORKING_DAYS, or applying these rules to a
  new monthly salary file. Run reconcile.py for the end-to-end pipeline.
---

# PF + ESI Salary Reconciliation

Consolidated from `PF_SALARY_RECONCILIATION_SKILL_v4.md` + `SKILL_PATCH_minimum_wage_floor.md`.
Re-run every month on the new salary sheet.

## Golden Rules (never violated)
1. **Salary PF must equal ECR PF** (per employee, after adjustment).
2. **Salary ESIC must equal Future-sheet ESIC** (per employee).
3. **NET PAYABLE NEVER CHANGES** — for every rule/pass. All differences are absorbed
   via OTHER DEDUCTION (PF side) or REVISED_ATTENDANCE_ALLOWANCE (ESI side).

## Inputs
- **Salary sheet** (xlsx): pan-India monthly file, header typically on row 5 (`header=4`).
  Key cols: `EMPCODE`, `FULLNAME`, `SITECODE`, `SITESTATE`, `SITEDIVISIONDAYS`,
  `NORMALDAYS`, `FIXED_BASIC`, `FIXED_DA`, `BASIC`, `DA`, `PF WAGES`, `PF`,
  `ESI WAGES`, `ESIC`, `OTHER DEDUCTION`, `GROSS AMT`, `NETPAYABLE`, `PF NO`, `UAN NO`.
- **ECR file(s)** (xlsx/csv): one or more 19-col FORMAT files (one per client/site).
  Match key `EMP CODE` → `EE` (employee PF). Header may be on row 1 or 2.
- **Future reference sheet** (xlsx): tab `FR_sheet`, header on **row 3**, data row 4+.
  `EMPCODE` (col G), `SITECODE` (col B/D), **ESIC employee = col Q (17)** — the ESI target.

**EMPCODE cleaning:** strip `.0` suffix on both sides before matching.

## Day-column semantics (read before any sanity check)
- `NORMALDAYS` = days actually worked (drives paid BASIC/DA/GROSS).
- `SITEDIVISIONDAYS` = divisor the FIXED_* rates are expressed at (1, 26, 27, 28, 30, 31).
- `DAILY_BASIC_RATE = FIXED_BASIC / SITEDIVISIONDAYS`; `BASIC = DAILY_BASIC_RATE × NORMALDAYS`.
- Full-month equivalent uses calendar days (April = 30). **Never hardcode 30 for the rate divisor.**

## ECR merge (CRITICAL)
Each ECR file contains **duplicate rows per employee**. Within each file
**deduplicate by EMP CODE first**, THEN concat across files and **sum EE** by EMP CODE
(different files = different registrations, e.g. Delhi+Punjab+Mumbai). Verify total
against the known EPFO figure; a 2–3× total means dedup was skipped.

## Multi-site employees
Same EMPCODE may appear in several salary rows (different sites). PF may be in one or
several rows; ECR has ONE aggregate per employee. Identify the **main PF row**
(row whose PF matches ECR ±₹1, else highest PF). Secondary PF rows → PF=0, parked in
OTHER_DED (`MULTI_SITE_SECONDARY_PF`). Zero-PF rows untouched (`MULTI_SITE_ZERO_PF`).

## The Four PF Rules (main rows / single-site)
`FIXED_BASIC_DA = FIXED_BASIC + FIXED_DA`
- **Case B** — `ECR_PF < ORIG_PF` and `FIXED_BASIC_DA ≤ 15000`: back-calc days
  `ADJ_DAYS = (ECR_PF/(FIXED_BASIC×0.12))×SITEDIVISIONDAYS`; reduce BASIC proportionally;
  `PF=ECR_PF`; `OTHER_DED += ORIG_PF−ECR_PF`; GROSS −= basic reduction.
- **Case A** — `ECR_PF < ORIG_PF` and `FIXED_BASIC_DA > 15000`: `PF=ECR_PF`;
  `OTHER_DED += ORIG_PF−ECR_PF`; days/basic/gross unchanged.
- **Cond 2** — `ECR_PF > ORIG_PF`: `PF=ECR_PF`; `OTHER_DED -= ECR_PF−ORIG_PF`
  (may go negative); basic/days/gross unchanged.
- **Not in ECR** — `ECR_PF == 0`: `BASIC=15001`; `OTHER_DED += ORIG_PF`; `PF=0`.
- `abs(ECR_PF−ORIG_PF) ≤ 1` → No Adjustment. `ORIG_PF==0 and ECR_PF==0` → NO_PF skip.

## PF post-passes (in order)
1. **12% Basic Fix** (No-Adjustment rows where `round(REVISED_PF/0.12) > REVISED_BASIC`):
   bump REVISED_BASIC up to `round(REVISED_PF/0.12)`, add delta to REVISED_GROSS,
   OTHER_DED and TOTAL_DED (NET cancels). Other rules already satisfy 12% — don't re-bump.
2. **Min-Wage Floor** (`REVISED_PF>0`): `MW_FLOOR = (BASIC/NORMALDAYS) × ADJ_WORKING_DAYS`;
   if `REVISED_BASIC < MW_FLOOR − 0.5`: lift to floor, recompute `REVISED_PF = round(0.12×(REVISED_BASIC+REVISED_DA),2)`; remark `[MW_FLOOR_APPLIED]`. Floor lifts, never lowers.
3. **Enforce REVISED_PF = 12%(REVISED_BASIC+DA)** for `REVISED_PF>0` outside ±0.1%:
   target `BASIC = round(REVISED_PF/0.12)`.
   - If target ≥ min-wage floor: set REVISED_BASIC = target, absorb delta in
     REVISED_ATTENDANCE_ALLOWANCE (GROSS/NET unchanged).
   - **If target < min-wage floor AND row is below ceiling (FIXED_BASIC+DA ≤ 15000):
     REDUCE `ADJ_WORKING_DAYS = floor(target / daily_rate)`** so the floor drops to
     permit basic = target (per-day minimum-wage rate preserved, only days fall) — e.g.
     PF pinned to ECR ₹900 with basic stuck at the ₹8000 floor → reduce days so basic = ₹7,500
     and 12% lands exactly ₹900. Note `DAYS_REDUCED_FOR_12PCT`.
   - Above-ceiling Case-A earners keep high basic with capped PF (12% relaxes by design).
   - Skip `REVISED_PF==0` (preserves Not-in-ECR rows).
4. **Integer days:** `ADJ_WORKING_DAYS = clip(1,31).astype(int)`.

## ESI passes (on the PF-reconciled book; April FULL_MONTH=30)
- **E1** primary-site alignment: per employee, primary = sitecode match (else max ESI WAGES);
  primary `REVISED_ESIC = Future_ESI`, `ESIC_AS_PER_FUTURE = Future_ESI`; secondaries = 0; clear DIFFERENCE col.
- **E1b** unmatched cleanup: employees not in Future → REVISED_ESIC=0; shift removed ESI
  (`orig_esic − current`) into OTHER_DEDUCTION so NET holds.
- **E2** PF ceiling: rows `ECR_PF==0 & GC>0 & (B+D)×31/GC < 15000` → `GC = floor((B+D)×31/15001)`.
- **E2b** ESI ceiling: rows `REVISED_ESIC==0 & GC>0 & GROSS×FULL_MONTH/GC ≤ 21000` →
  `GC = floor(GROSS×FULL_MONTH/21001)`; clamp every GC ≤ FULL_MONTH.
- **E3** negative OTHER_DED → ATT_ALW: `GF += |OD|; OD=0; GROSS=B+D+GF; TOTAL_DED += |OD|`.
- **E4** balancer: if `GROSS − TOTAL_DED ≠ NET`: `GF += NET−(GROSS−TOTAL_DED)`; recompute GROSS. Only GF moves.

## Rule M7 — Day anchoring to the FIXED rate (no absurd projections)
**Anchors are inviolable: `REVISED_PF == ECR_PF` and `REVISED_ESIC == Future ESI` per employee, ALWAYS — never capped/zeroed.** Ceiling compliance is via DAYS, never by changing PF/ESI.

`ADJ_WORKING_DAYS` must be set from the worker's **real rate**, so the implied full-month figure
(`MONTHLY_*_PROJECTION = REVISED_* × FULL_MONTH / ADJ_WORKING_DAYS`) equals his actual wage and never
explodes. **Do NOT** slash days or inflate attendance allowance to *manufacture* a >₹21,000 / >₹15,000
projection — that turns a real ₹15,000/month worker into an implied ₹1,00,000, which is nonsense.
```
PF>0 : ADJ = round((REVISED_BASIC+REVISED_DA) × SITEDIVISIONDAYS / FIXED_BASIC)
ESI>0: ADJ = round(REVISED_GROSS × SITEDIVISIONDAYS / FIXEDGROSS)
else : ADJ = round(REVISED_GROSS × SITEDIVISIONDAYS / FIXEDGROSS)        # use the real rate
clamp ADJ to [1, FULL_MONTH];  M6 may only RAISE days so a PF row projects BD ≤ ₹15,000.
```
**Flag, don't fake — `ANOMALY_BELOW_CEILING`:** where the real full-month rate (`FIXEDGROSS×FM/SDD`)
is ≤ ₹21,000 but the employee is **not** in ESI (or `FIXED_BASIC×FM/SDD` ≤ ₹15,000 but not in PF), the
row is a register inconsistency (he *should* be covered). Keep the realistic projection and set the
flag for manual review — do NOT distort days/allowances to hide it. Designation/job-title is irrelevant.

## Final normalization
- **ECR_PF cap:** `ECR_PF_OUT = min(ECR_PF_filed, REVISED_PF)`.

## Validation set (must hold)
C1 OTHER_DED ≥ 0 · C2 |REVISED_NET − NET| ≤ 1 · C3 |REVISED_PF − 12%(B+D)| ≤ 1 on PF>0 ·
C4 ESI=0.75%×GROSS (informational; relaxes when ESI=Future conflicts) · C5 ATT_ALW ≥ 0 ·
C6 TOTAL_DED ≥ 0 · C7 |GROSS−(B+D+ATT)| ≤ 1 · C9 ADJ_WORKING_DAYS ∈ [1,31] ·
C10 ECR_PF_capped ≤ REVISED_PF · C-MW REVISED_BASIC ≥ MW_FLOOR on PF>0 · C-INT days integer.
Per-employee: Σ REVISED_PF = ECR_PF (₹0 gap); Σ REVISED_ESIC ≈ Future total (gap = Future-only employees).

## Outputs (two deliverables, mirror prior months)
1. **`<Mon>26_Reconciliation_Report.xlsx`** — Summary, PF_Audit, ESI_Audit, Math_Checks, Reconciled_Data.
2. **`<Mon>26_Final_Complete.xlsx`** — original salary columns + **24 appended audit columns**
   (drop duplicate `ESIC.1`):
   `ADJ_WORKING_DAYS, REVISED_BASIC, REVISED_DA, REVISED_ATTENDANCE_ALLOWANCE, REVISED_GROSS,
   ECR_PF, REVISED_PF, REVISED_ESIC, Future_ESI, ESIC AS PER FUTURE, ESI DIFFERENCE (Future-REVISED),
   REVISED_OTHER_DEDUCTION, REVISED_TOTAL_DED, REVISED_NET_PAYABLE, NET_PAYABLE_DIFF, RULE_APPLIED,
   NOTES, %, remark, 12% OF (REVISED_BASIC+DA), DIFF (12%_PF vs REVISED_PF), REVISED_%,
   MONTHLY_BD_PROJECTION, MONTHLY_GROSS_PROJECTION`.
   Audit columns `12% OF …`, `DIFF …`, `REVISED_%` are written as **live Excel formulas**.

## Usage
```
python reconcile.py \
  --salary  apr26_FULL_monthly_sheet.xlsx \
  --ecr     FORMAT-APRIL_2026_DELHI.xlsx FORMAT_APRIL_2026_STEAGE.xlsx FORMAT-APRIL_2026_DMART.xlsx \
  --future  "Future reference sheet_2604.xlsx" \
  --month   2026-04 \
  --salary-header 4 \
  --out-prefix April26
```
(`--ecr` accepts one already-merged ECR file or several per-client files; the script dedups+sums.)
Run on the user's machine where the full salary file is local — the Drive download tool caps at 10 MB.
