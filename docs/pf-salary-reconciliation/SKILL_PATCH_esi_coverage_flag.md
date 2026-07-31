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
actually pay ESI. Keyed correctly on **`ESIC = 0`** (with wages earned), the gap on
the first-cut basis was 187; **on the corrected basis below it is 36** (see the
2026-07-31 refinement).

### Day-column basis (REFINED 2026-07-31 — REVISED_GROSS_NEW ÷ NORMALDAYS)

Full-month gross for the ₹21,000 test uses the **ESI base** and the **actual days
worked**, per the SKILL.md "Day-Column Semantics" rule (earned amount ÷ actual days
worked × calendar days in month — never SITEDIVISIONDAYS, never a hardcoded 30):

```
FULL_MONTH_GROSS = (REVISED_GROSS_NEW / NORMALDAYS) × CALENDAR_DAYS   # Apr=30, etc.
```

- **Amount = REVISED_GROSS_NEW**, not FIXEDGROSS or raw GROSS AMT. This is the M8 ESI
  base (REVISED_GROSS minus the ESI-ineligible allowances — washing, conveyance,
  transport, travelling, uniform, attire, mobile/vehicle reimbursement, LTA — with
  HRA retained). The ₹21,000 ceiling is an ESI-wage ceiling, so the test must run on
  the ESI wage, not the full gross.
- **Divisor = NORMALDAYS, capped at calendar days** (`round().clip(1, CALENDAR_DAYS)`).
  A part-month worker is projected to their true full-month equivalent; a full-month
  earner (NORMALDAYS ≥ days-in-month — e.g. 31 when paid holidays/weekly-offs push it
  past a 30-day April) must **not** be projected DOWN, so attendance is capped at the
  calendar month. Without the cap, a ₹21,001 full-month earner would divide to ₹20,323
  and be wrongly flagged. `SITEDIVISIONDAYS` is only the FIXED-rate divisor and must
  NOT be used here.
- Supersedes the earlier "FIXEDGROSS / SITEDIVISIONDAYS × calendar days" basis, which
  over-stated eligibility (187) by testing the full fixed gross instead of the ESI wage.

### The Rule

```
FULL_MONTH_GROSS = (REVISED_GROSS_NEW / NORMALDAYS) × CALENDAR_DAYS
ESI_ELIGIBLE     = 0 < FULL_MONTH_GROSS <= 21000
WAGES_EARNED     = GROSS_AMT > 0                     # earned wages this month (no wages -> no ESI due)
ESI_DEDUCTED     = ESIC > 0                          # ESIC = ESI actually deducted in the salary sheet

ESI_COVERAGE_GAP = ESI_ELIGIBLE and WAGES_EARNED and not ESI_DEDUCTED
```

Note on the M4a option: for a genuine full-month worker projecting ≤ ₹21,000, the
skill's M4a rule *can* raise REVISED_ATTENDANCE_ALLOWANCE to lift the ESI base above
₹21,000 (absorbed in OTHER_DEDUCTION, NET unchanged) and reconcile them as out of ESI.
Decision on the Apr-2026 book: **do NOT apply the lift — keep the 36 flagged as genuine
enrolment gaps.** The flag stays a flag; the M4a lift is not applied by the pipeline.

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

Progression of the flag as each correction was applied (all keyed on `ESIC = 0` +
wages earned; monetary columns untouched throughout):

| Basis | Flags |
|---|--:|
| `~ie` Future-sheet membership (original misfire) | 12,650 |
| `FIXEDGROSS / SITEDIVISIONDAYS × 30` (first cut) | 187 |
| `REVISED_GROSS_NEW / NORMALDAYS × 30` (raw days) | 40 |
| **`REVISED_GROSS_NEW / NORMALDAYS(clip ≤30) × 30` (final)** | **36** |

- The 36 are genuine near-full-month workers whose ESI-base wage still projects
  ≤ ₹21,000 — real enrolment gaps to regularise.
- The 151 that dropped (187 → 36) were rows whose *full fixed gross* was ≤ ₹21,000
  but whose *ESI wage* (gross minus ineligible allowances) or real-attendance
  projection actually clears the ceiling — never true gaps.
- The last 4 (40 → 36) are full-month earners with NORMALDAYS = 31 and
  REVISED_GROSS_NEW ≥ ₹21,001; capping attendance at the calendar month stops their
  wage being projected DOWN below the ceiling.
- Rows with `GROSS_AMT = 0` (no attendance) are correctly **not** flagged.
- Flag/ACTION_REASON only — PF gap **0**, NET **₹25,99,37,250 unchanged**.

### Where to Apply

Compute `REVISED_GROSS_NEW` (the M8 ESI base) **first**, then set the coverage-gap
flag at the point where ACTION_REASON is assigned (after ESI passes E1–E4). Keyed on
the salary sheet's original `ESIC = 0` — never `REVISED_ESIC` or `~ie`. Implemented in
`month_pipeline.py::post_and_validate` (REAL_FULL_MONTH_GROSS = REVISED_GROSS_NEW /
NORMALDAYS × calendar days). The coverage-gap list should carry per row: `EMPCODE,
SITECODE, SITESTATE, NORMALDAYS, REVISED_GROSS_NEW, FULL_MONTH_GROSS, ESI_WAGES,
EST_ESI_EMPLOYEE (0.75%), EST_ESI_EMPLOYER (3.25%)`.
