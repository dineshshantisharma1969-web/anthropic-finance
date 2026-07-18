---
type: rule
domain: salary
ref: wage-code-50pct
title: Wage Code 50% rule — BASIC+DA must be ≥ 50% of gross
effective_from: 2025-12-01
effective_to:
status: active
supersedes:
superseded_by:
source: Code on Wages 2019 (wage definition) · ISPL policy Jul-2026
based_on: "[[10-Law/PF-ESI/README]]"
tags: [wage-code, basic, gross, salary, compliance]
created: 2026-07-18
---

# Wage Code 50% rule — BASIC+DA must be ≥ 50% of gross

## Rule

An employee's **FIXED_BASIC + FIXED_DA must be at least 50% of monthly fixed gross**
(remuneration). If basic+DA is below 50% of gross, the wage structure is non-compliant and
must be restructured.

**Compliance basis is GROSS (remuneration), not CTC.** Testing against CTC massively
over-counts violations; the gross/remuneration basis is the correct statutory test.

**Day-rated employees — the critical treatment:**
- For day-rated staff, `FIXED_BASIC` is a **per-day rate**, not a monthly figure.
- Convert to monthly by multiplying by the **number of CALENDAR days in that month**
  (Dec = 31, Jan = 31, Feb = 28, Mar = 31) — **days in the month, NOT the NORMALDAYS /
  attendance figure.**
- Detection heuristic used: `ratio = CTC / FIXEDGROSS`; if `ratio ≥ 15` the row is day-rated.
- Then test: monthly (basic+DA) ≥ 50% of monthly gross.

**Fixing a violation (goal-seek, net-neutral):**
- Raise the revised basic until `basic+DA = 50%` of the final gross (an inner goal-seek loop,
  because gross itself rises with basic; it converges to `lift L = gross − 2·(basic+DA)`).
- **Allowances are NOT reduced** — they are tied to the ESI base (`REVISED_GROSS_NEW`); cutting
  them would understate ESI. See [[net-payable-sacrosanct]].
- **Raise OTHER DEDUCTION** by `(basic lift − PF increase)` so **net payable is unchanged**
  ([[pf-golden-rules]]).
- PF recomputed at 12% with the ₹15,000 ceiling ([[pf-contribution-basis]]).

## Why / basis

The Code on Wages defines "wages" so that excluded allowances cannot exceed 50% of total
remuneration — i.e. basic+DA must be ≥ 50%. Keeping basic artificially low to suppress
PF/gratuity/bonus is what the rule targets. The gross basis and calendar-day conversion make
the test reflect actual monthly remuneration.

## Worked example

Day-rated employee, Feb-26: FIXED_BASIC ₹300/day → monthly basic = 300 × 28 = ₹8,400. If
monthly gross = ₹20,000, basic+DA must be ≥ ₹10,000. Goal-seek lifts basic so basic+DA = 50%
of the new gross; OTHER DEDUCTION rises by (lift − extra PF); net payable holds; row lands at
exactly 50.00%.

## Applied in

- [[40-Workings/2026-07-wage-code-50pct-dec-mar]]
