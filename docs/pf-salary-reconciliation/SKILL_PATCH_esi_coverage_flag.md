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

The earlier flag keyed on **`REVISED_ESIC = 0`** — the *reconciled/revised* ESI
value. That is wrong: the ESI passes legitimately set `REVISED_ESIC = 0` on many
rows (secondary multi-site rows, Future-register alignment) **even when the
employee actually had ESI deducted in the salary sheet**. Keying on `REVISED_ESIC`
therefore flags people who are **already covered**.

In April 2026 this over-flagged badly: **1,940** rows were flagged, but **1,886**
of them already had ESI deducted (`ESIC > 0`). The true gap was **541** — and the
old rule caught only ~54 of them, **missing ~487 genuine gaps**.

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
ESI_DEDUCTED     = ESIC > 0                          # ESIC = ESI actually deducted in the salary sheet

ESI_COVERAGE_GAP = ESI_ELIGIBLE and not ESI_DEDUCTED
```

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
- **True coverage gap (`ESI_ELIGIBLE and ESIC = 0`): 541** — est. ESI (emp+employer)
  ≈ **₹3.37 L/month**
- Old flag: 1,940 → **1,886 false positives removed, ~487 genuine gaps recovered**
- PF gap **0**, NET **₹25,99,37,250 unchanged** after the correction.

### Where to Apply

Replace the old coverage-gap flag step (the one keyed on `REVISED_ESIC = 0`) at the
point where ACTION_REASON is assigned, after the ESI passes E1–E4. The output the
coverage-gap list should carry per row: `EMPCODE, SITECODE, SITESTATE, NORMALDAYS,
SITEDIVISIONDAYS, FIXEDGROSS, FULL_MONTH_GROSS, ESI_WAGES, EST_ESI_EMPLOYEE (0.75%),
EST_ESI_EMPLOYER (3.25%)`.
