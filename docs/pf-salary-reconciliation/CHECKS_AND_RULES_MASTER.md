# PF / ESI Reconciliation — Master Reference (Checks C1–C13 + Rules M1–M17 + Patches)

**The single consolidated reference.** Everything that was scattered across the
canonical skill doc, the v3/v4/v4.1 addenda, and the individual SKILL_PATCH files is
gathered here. Last consolidated: 2026-07-31.

> Sources folded in: `SKILL.md`, `PF_SALARY_RECONCILIATION_SKILL_v4.md` (Drive, 86 KB
> canonical), `SKILL_PATCH_esi_coverage_flag.md`, `SKILL_PATCH_minimum_wage_floor.md`,
> `v3_projection_addendum_for_skill.md`, `reconcile.py`, `month_pipeline.py`. Where a
> rule is only partially documented, that is stated explicitly — nothing is invented.

---

## 0. Golden Rules (never violated)
1. **Σ REVISED_PF = ECR_PF** per employee (₹0 gap).
2. **Σ REVISED_ESIC = Future-sheet ESIC** per employee.
3. **NET PAYABLE never changes** — every adjustment is absorbed via OTHER_DEDUCTION or
   ATTENDANCE_ALLOWANCE. Net payable is what was actually paid; it is sacrosanct.

## 1. Day-column semantics (applies to every projection)
Three different "day" numbers — never interchange, never hardcode 30:
- `NORMALDAYS` / `ADJ_WORKING_DAYS` — actual (or adjusted) days worked → the divisor for "earned per day".
- `SITEDIVISIONDAYS` — the site's **rate divisor** (1/24/26/27/28/30/31) → `DAILY_RATE = FIXED_BASIC / SITEDIVISIONDAYS`.
- Calendar full-month days — 28/29 (Feb), 30 (Apr/Jun/Sep/Nov), 31 (rest) → the **multiplier** for full-month projection.

**Universal full-month formula:** `FULL_MONTH_EQUIVALENT = (EARNED_AMOUNT / NORMALDAYS_or_ADJ) × CALENDAR_DAYS`,
with `NORMALDAYS` **capped at the calendar month** (`round().clip(1, CALENDAR_DAYS)`) so a
full-month earner (e.g. NORMALDAYS = 31 via paid holidays) is never projected DOWN.

---

## 2. Base four PF rules (pre-M layer)
Pre-compute per PF-anchor row: `ORIG_PF`, `ECR_PF`, `FIXED_BASIC_DA = FIXED_BASIC + FIXED_DA`.

| Rule | Trigger | Action (NET always unchanged) |
|---|---|---|
| **1 — Case B** | ECR_PF < ORIG_PF and FIXED_BASIC_DA ≤ 15,000 | back-calc `ADJ_DAYS = (ECR_PF/(FIXED_BASIC×0.12))×SITEDIVISIONDAYS`; reduce BASIC proportionally; PF=ECR_PF; OTHER_DED += PF_DIFF |
| **2 — Case A** | ECR_PF < ORIG_PF and FIXED_BASIC_DA > 15,000 | days/BASIC unchanged; PF=ECR_PF; OTHER_DED += PF_DIFF |
| **3 — Not in ECR** | ECR_PF = 0 | OTHER_DED += ORIG_PF; PF=0; BASIC=15001 (flag) |
| **4 — Cond 2** | ECR_PF > ORIG_PF | PF=ECR_PF; OTHER_DED −= PF_DIFF (may go negative, cleaned by M5) |

**Multi-site:** main PF row matches ECR (±₹1) else highest PF (v4 M1: max-NORMALDAYS row);
secondaries → PF=0, parked in OTHER_DED; zero-PF rows untouched.

---

## 3. Field rules M1–M17

| # | Rule | Status |
|---|---|---|
| **M1** | Multi-site primary PF row = **MAX NORMALDAYS** row (reassign ECR there); move preserves NET on both rows | ✅ defined |
| **M2** | **Statutory caps** (0 violations): PF ≤ ₹1,800 · B+D ≤ ₹15,000 (surplus→ATT_ALW) · ESI>0 GROSS ≤ ₹21,000 (else zero ESI→OTHER_DED) · ECR_PF ≤ REVISED_PF | ✅ defined |
| **M3** | **Both-direction projection caps** (employee-level P1–P4): in-PF ⇒ B+D proj ≤ 15k (raise days); not-in-PF ⇒ > 15k (reduce days); in-ESI ⇒ GROSS proj ≤ 21k (raise days); not-in-ESI ⇒ > 21k (reduce days) | ✅ defined |
| **M4** | **Conflict-row plug lifts** — M4a ATT_ALW lift (GROSS too low, days maxed) · M4b BASIC lift (B+D too low) · M4c GROSS cap (in-ESI secondary > 21k) | ✅ defined |
| **M5** | **Negative-plug cleanup**: neg ATT_ALW → 0, deduct from BASIC (GROSS held); neg OTHER_DED → 0, lift ATT_ALW+GROSS (NET held) | ✅ defined |
| **M6** | **ECR_PF > 0 ⇒ (B+D) full-month proj ≤ ₹15,000** (raise days only; = check C10) | ✅ defined |
| **M7** | **ADJ_WORKING_DAYS by FIXED-rate anchoring** — anchor days to the real rate (FIXED_BASIC/FIXEDGROSS ÷ SITEDIVISIONDAYS) so projections never explode; do NOT fake days | ✅ defined |
| **M8** | **ESI base = REVISED_GROSS_NEW** = REVISED_GROSS − ESI-ineligible allowances (washing, conveyance, transport, travelling, uniform, attire, mobile/vehicle reimb, LTA), **HRA retained** as the balancing figure; backsolve to REVISED_ESIC/0.0075 for in-ESI rows | ✅ defined |
| **M9** | Referenced only as "M6/M7/M8/M9 → projection recompute" — **no standalone rule text** | ⚠️ named only |
| **M13** | **13th-month annual true-up**: PF = 12% on (BASIC+DA); ECR>0 → REVISED_BASIC = ECR/0.12 − DA (plug to attendance allowance); ECR=0 → project above ₹15,000 via day-reduction then basic lift. GROSS/PF/NET held. Sub-tag `M13c_BASIC_LIFT`. | ✅ defined (annual pass) |
| **M14** | Observed build tag `M14_WASHING_EXCL` — exclude washing (& other listed) allowances from the ESI base. Function = the M8 `ESI_EXEMPT` exclusion. | ◐ inferred from tag |
| **M15** | Observed build tag `M15_OUTESI_CEILING` — out-of-ESI rows adjusted so the ESI-base projection clears ₹21,000 (M3-P4 / ESI Scenario 4). | ◐ inferred from tag |
| **M16** | Observed build tags `M16a_CAPPED_AT_GROSS` (cap projection at actual gross) and `M16b_SUPPRESSED_LOW_DAYS` (suppress implausible low-day projections). Related to the projection cap (§5). | ◐ inferred from tag |
| **M10, M11, M12, M17** | **No rule text and no build tag found** in any source. | ✗ undefined |

> M9–M17 honesty note: only M13 is formally documented (annual true-up). M14/M15/M16
> are **inferred from the build-tag names** in `*_M13_FINAL` / `*_M12_M15` / `*_M16_PATCHED`
> outputs — their exact logic is not written down. M10/M11/M12/M17 do not appear anywhere.
> The "M12/M15/M16" in filenames are build/version tags, not necessarily rule numbers.
> **Do not invent checks for the undefined ones** — supply the source note and recompile.

---

## 4. ESI coverage-gap flag (corrected — final basis)
Flags employees who **should be in ESI but were not deducted** (to enrol/regularise).
```
ESI_BASE          = REVISED_GROSS_NEW                       # M8 base (gross − ineligible allow., HRA kept)
DAYS              = round(NORMALDAYS).clip(1, CALENDAR_DAYS) # cap a full-month earner
FULL_MONTH_GROSS  = ESI_BASE / DAYS × CALENDAR_DAYS
ESI_COVERAGE_GAP  = (ESIC == 0) and (GROSS_AMT > 0) and (0 < FULL_MONTH_GROSS <= 21000)
```
- Keyed on **actual ESI deducted (`ESIC = 0`)** — never `REVISED_ESIC` or Future-sheet
  membership (`~ie`), which flag people who actually pay ESI.
- Flag-only: no monetary column moves. (Optional M4a lift can reconcile a row out of ESI,
  but the standing decision is to **keep them flagged**, not lift.)
- Apr-2026 M13 progression: `~ie` 12,650 → FIXEDGROSS/SITEDIVISIONDAYS 187 →
  REVISED_GROSS_NEW/NORMALDAYS 40 → **NORMALDAYS capped ≤ cal-month = 36 (final)**.
- Implemented in `month_pipeline.py::post_and_validate` and `reconcile.py` (`ANOMALY_BELOW_CEILING`).

## 5. Other post-passes (patches)
- **12% basic fix** — adjust BASIC so `REVISED_PF = 12%×(BASIC+DA)` exactly; ATT_ALW absorbs (C3).
- **Minimum-wage floor** — `MW_BASIC_FLOOR = (BASIC/NORMALDAYS)×ADJ_WORKING_DAYS`; if
  `REVISED_BASIC < MW_BASIC_FLOOR` and PF>0, lift BASIC to the floor and recompute PF. Floor lifts, never lowers.
- **Integer days** — ADJ_WORKING_DAYS always a whole integer in [1, FULL_MONTH]; use `floor` on reductions.
- **MONTHLY_GROSS_PROJECTION cap** — after all passes, for active rows raise days only:
  `target = floor(REVISED_GROSS × FULL_MONTH / 21001)`, `ADJ = max(current, clamp(target,1,FULL_MONTH))`,
  so a low-day row can't imply an absurd (₹1L+) monthly wage. Touches ADJ_WORKING_DAYS only.
- **Projection columns (v3)** — computed on `REVISED_GROSS_NEW (final)`, not REVISED_GROSS;
  recompute from stored `REVISED_GROSS_NEW` + `ADJ_WORKING_DAYS` (self-consistent), not the old stored projection.
- **ESI passes E1–E4** — E1 primary-site alignment · E1b unmatched cleanup + OTHER_DED rebalance ·
  E2/E2b PF/ESI day-ceiling reductions · E3 negative-OTHER_DED shift into GROSS · E4 final balance (GG−HI=HJ).

---

## 6. Validation set — C1–C13 (+ C-MW, DAY-BASIS)
All must be **0 violations** on the filed workbook unless marked informational.

| Check | Rule | Notes |
|---|---|---|
| **C1** | OTHER_DEDUCTION ≥ 0 | holds after M5 cleanup (Cond 2 may be transiently negative) |
| **C2** | \|NET − (GROSS − TOTAL_DED)\| ≤ 1 | arithmetic identity |
| **C3** | \|PF − 12%×(BASIC+DA)\| ≤ 1, on PF>0 | the 12% rule |
| **C4** | MONTHLY_GROSS_PROJECTION sane (no absurd ₹1L+) | informational; enforced by the projection cap (§5) |
| **C5** | REVISED_ATTENDANCE_ALLOWANCE ≥ 0 | |
| **C6** | REVISED_TOTAL_DED ≥ 0 | |
| **C7** | \|GROSS − (BASIC+DA+ATT_ALW)\| ≤ 1 | gross foots |
| **C8** | \|REVISED_NET_PAYABLE − NETPAYABLE\| ≤ 1 | = Golden Rule 3 |
| **C9** | ADJ_WORKING_DAYS ∈ [1, FULL_MONTH] | active PF/ESI rows; zero-activity rows at 0 days are legitimate |
| **C10** | ECR_PF>0 ⇒ (BASIC+DA)×FULL_MONTH/ADJ ≤ 15,000 | statutory PF ceiling (= M6) |
| **C11** | PF=0 ⇒ (BASIC+DA)×FULL_MONTH/ADJ > 15,000 | self-consistency: absence from PF justified |
| **C12** | ESI>0 ⇒ **REVISED_GROSS_NEW** ≤ 21,000 | statutory ESI ceiling — test the **ESI base**, not full gross (see below) |
| **C13** | ESI=0 ⇒ REVISED_GROSS×FULL_MONTH/ADJ > 21,000 | self-consistency: absence from ESI justified |
| **C-MW** | REVISED_BASIC ≥ minimum-wage floor | on PF>0 rows |
| **DAY-BASIS** | day-tinker derivations use per-row SITEDIVISIONDAYS, never a hardcoded 30 | ties better on non-30-day sites |

> Note: C1 and the base Cond-2 rule ("OTHER_DED may go negative") are reconciled by M5 —
> negatives are transient and cleaned in the final pass, after which C1 holds.

### C12 must test REVISED_GROSS_NEW, not REVISED_GROSS
₹21,000 is an **ESI-wage** ceiling, so the test runs on the ESI base (M8's
`REVISED_GROSS_NEW` = gross − ESI-ineligible allowances, HRA retained) — the same
principle as the ESI coverage-gap flag. Testing full `REVISED_GROSS` over-states
violations by counting ineligible allowances against the ceiling.

Because M8 sets `REVISED_GROSS_NEW = REVISED_ESIC / 0.0075` on every ESI row
(verified: 9,210/9,210 rows in May-26), C12 is **arithmetically identical to
`REVISED_ESIC ≤ ₹157.50`** (0.75% × 21,000) — the ESI twin of M2's ₹1,800 PF cap.

Any residual is **ESI filed above the statutory cap in the Future sheet**, not a
computation error. Golden Rule 2 pins `REVISED_ESIC` to the Future sheet, so these
cannot be reduced in the reconciliation — they are a reconciling item exactly like
the above-cap ECR PF rows under M2/C10. Escalate to whoever files ESI.

| Month | C12 on REVISED_GROSS | C12 on REVISED_GROSS_NEW (correct) | excess employee ESI |
|---|--:|--:|--:|
| April-26 | 40 | **20** | ₹348/month |
| May-26 | 1,069 | **877** | ₹25,742/month |

---

## 7. Pipeline order (v4)
1. Re-allocate PF to MAX-NORMALDAYS row (M1) → 2. ESI Future dedup → 3. PF strict cap ₹1,800
(M2) → 4. ECR_PF ≤ REVISED_PF → 5. ESI strict cap GROSS≥21k (M2) → 6. Day adjustment
feasible-range (M3/M6/M7) → 7. ATT_ALW lift (M4a) → 8. BASIC lift (M4b) → 9. in-PF B+D cap
multi-site → 10. in-ESI GROSS cap (M4c) → 11. negative-plug cleanup (M5) → 12. 12% fix (C3)
→ min-wage floor → 13. ESI base / GROSS_NEW (M8) + projection recompute + ESI coverage-gap flag.

## 8. Where each thing is implemented
- `reconcile.py` — Golden Rules, base 4 rules, M1–M7, min-wage floor, ESI passes E1–E4, `ANOMALY_BELOW_CEILING`, C1–C10.
- `month_pipeline.py` — M8 (REVISED_GROSS_NEW), ESI coverage-gap flag (final basis), C1–C10 re-validation, ERP load.
- Vault (`salary-wiki`): `wiki/M_Rules_PF_ESI_Reconciliation.md` (M1–M8), `raw/company/pf_reco_case_rules.md` (base 4).

*This file supersedes the individual scattered patches for day-to-day reference. When a
new rule/rate lands, update it here in the same commit.*
