---
type: rule
domain: salary
ref: net-payable-sacrosanct
title: Net payable is sacrosanct — how differences are absorbed
effective_from: 2025-04-01
effective_to:
status: active
supersedes:
superseded_by:
source: PF_SALARY_RECONCILIATION_SKILL_v4 · ISPL policy
based_on: "[[pf-golden-rules]]"
tags: [net-payable, other-deduction, esi, allowances, invariant]
created: 2026-07-18
---

# Net payable is sacrosanct — how differences are absorbed

## Rule

Whenever a reconciliation or restructuring changes the internal composition of a salary
(basic ↑, PF ↑, days changed), **NET PAYABLE must not move**. The mechanics:

1. **If you raise the revised basic, raise OTHER DEDUCTION** by the same amount less the extra
   PF it creates: `ΔOTHER_DEDUCTION = basic lift − ΔPF`. This holds net payable exactly.
2. **Allowances CANNOT be reduced.** They are tied to the ESI calculation base
   (`REVISED_GROSS_NEW`); cutting an allowance would understate the ESI wage and the filing.
3. **ESI exclusions** are read exactly as the sheet computes them — the "second option is safe"
   basis: `ESI base = GROSS − STATUTORY_EXCL_TOTAL − EXTRA_EXCL`, i.e. `REVISED_GROSS_NEW (final)`.

## Why / basis

The employee was paid a certain net amount; that is a historical fact and cannot be rewritten.
Reconciliation and wage-code restructuring only rearrange the *composition* (to match ECR, or to
hit the 50% basic threshold) — the take-home and the ESI base are both preserved so no new
liability or filing mismatch is created.

## Worked example

Restructuring lifts basic by ₹1,000. PF rises by ₹120 (12%, under ceiling). OTHER DEDUCTION is
raised by ₹880. Net payable: unchanged. Allowances: untouched. ESI base: unchanged.

## Applied in

- [[40-Workings/2026-07-wage-code-50pct-dec-mar]]
- [[40-Workings/2026-07-pf-reconciliation-fy2526]]
