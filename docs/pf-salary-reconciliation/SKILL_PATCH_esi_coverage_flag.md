# Skill Patch — ESI Coverage-Gap Flag (corrected basis)

This patch corrects how the **ESI "should be in ESI" coverage-gap flag** is decided.
Paste the section below into `pf-salary-reconciliation/SKILL.md`, replacing any
earlier "ESI-exempt but full-month ≤ ₹21,000" / coverage-gap flag wording. Insert
it in the ESI section, after the E1–E4 ESI passes.

Consolidated from the April-2026 reconciliation review (2026-07).

---

## ESI Coverage-Gap Flag (CRITICAL — corrected 2026-07)

### Rationale

ESI is compulsory for any employee whose **full-month gross ≤ ₹21,000** (the
eligibility ceiling; employee 0.75% + employer 3.25%). The reconciliation must
flag employees who are **eligible but not actually in ESI** — the coverage gap to
regularise.

The earlier flag keyed **coverage on Future-reference-sheet membership**
(`emp_in_esi`, `~ie` in `reconcile.py`; equivalently `REVISED_ESIC = 0`
downstream). That is wrong: the Future sheet lists only a **subset** of the ESI
population, and the ESI passes set `REVISED_ESIC = 0` on rows that **actually had
ESI deducted in the salary sheet**. So the flag fires on employees who are
**already covered**.

In April 2026 the `~ie` basis flagged **12,650** rows — most of them people who
actually pay ESI. Keyed correctly on **`ESIC = 0`** (with wages earned), the true
gap is **187**.

### Day-column basis (unchanged — do NOT alter)

Full-month gross for the ₹21,000 test is the existing `REAL_FULL_MONTH_GROSS`:

```
FULL_MONTH_GROSS = (FIXEDGROSS / SITEDIVISIONDAYS) × CALENDAR_DAYS   # Apr=30, etc.
```

`SITEDIVISIONDAYS` (1, 26, 27, 28, 30, 31) is the divisor the FIXED_* rates are
expressed at. **Do not replace this with "if per-day, × days-in-month"** — FIXEDGROSS
is not always per-day; at 26/27/28-day sites that shortcut over-states the full
month. Verified April 2026: `FIXEDGROSS / SITEDIVISIONDAYS × 30` equals the stored
`REAL_FULL_MONTH_GROSS` on all 21,152 rows.

### The Rule

```
FULL_MONTH_GROSS = REAL_FULL_MONTH_GROSS            # = FIXEDGROSS / SITEDIVISIONDAYS × calendar days
ESI_ELIGIBLE     = 0 < FULL_MONTH_GROSS <= 21000
WAGES_EARNED     = GROSS_AMT > 0                     # earned wages this month (no wages -> no ESI due)
ESI_DEDUCTED     = ESIC > 0                          # ESIC = ESI actually deducted in the salary sheet

ESI_COVERAGE_GAP = ESI_ELIGIBLE and WAGES_EARNED and not ESI_DEDUCTED
```

In `reconcile.py` this is the `ANOMALY_BELOW_CEILING` ESI term. The corrected code
keys it on the salary sheet's original `ESIC` (`OESIC_v == 0`), **not** on
`emp_in_esi` (`~ie`, Future-sheet membership) — the Future sheet lists only a
subset of the ESI population, so `~ie` flags employees who actually pay ESI.

- Flag `ESI_COVERAGE_GAP = True` rows: **"ESI applicable (full-month ≤ ₹21,000) but
  ESI not deducted — enrol / regularise."**
- **Never** flag a row with `ESIC > 0` — already covered, regardless of
  `REVISED_ESIC`.
- Above-ceiling (`FULL_MONTH_GROSS > 21000`) rows are **not** flagged. Caveat: an
  employee who crosses ₹21,000 **mid contribution-period** (Apr–Sep / Oct–Mar)
  stays covered for the rest of that period — do not treat a mid-period crossing as
  a reason to remove existing ESI.

### Why It's Safe

- Touches only the **flag / ACTION_REASON**, not a single monetary column.
- `REVISED_ESIC`, `Future_ESI`, `REVISED_GROSS`, `NETPAYABLE`, PF columns — all
  unchanged. Golden Rules (PF = ECR, NET unchanged, Σ REVISED_ESIC = Future) hold.

### Field-Tested Result — April 2026

- ESI-eligible (full-month ≤ ₹21,000): **16,953**
- Already deducted (`ESIC > 0`): 16,993
- **True coverage gap (`ESI_ELIGIBLE and GROSS_AMT > 0 and ESIC = 0`): 187** —
  est. ESI (emp+employer) ≈ **₹1.30 L/month**
- The `~ie` (Future-sheet) basis flagged **12,650** rows (misfire); the corrected
  `ESIC = 0` basis with the wages-earned filter = **187**. (354 eligible rows with
  `GROSS_AMT = 0` — no attendance this month — are correctly **not** flagged, since
  no wages means no ESI due this month.)
- PF gap **0**, NET **₹25,99,37,250 unchanged** after the correction.

### Where to Apply

Replace the old coverage-gap flag step (the one keyed on `REVISED_ESIC = 0`) at the
point where ACTION_REASON is assigned, after the ESI passes E1–E4. The output the
coverage-gap list should carry per row: `EMPCODE, SITECODE, SITESTATE, NORMALDAYS,
SITEDIVISIONDAYS, FIXEDGROSS, FULL_MONTH_GROSS, ESI_WAGES, EST_ESI_EMPLOYEE (0.75%),
EST_ESI_EMPLOYER (3.25%)`.
