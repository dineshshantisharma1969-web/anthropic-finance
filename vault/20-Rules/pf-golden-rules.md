---
type: rule
domain: salary
ref: golden-rules
title: The three Golden Rules of salary reconciliation
effective_from: 2025-04-01
effective_to:
status: active
supersedes:
superseded_by:
source: PF_SALARY_RECONCILIATION_SKILL_v4 · SALARY_KNOWLEDGEBASE.md §1
based_on: "[[10-Law/PF-ESI/README]]"
tags: [pf, esi, salary, invariant]
created: 2026-07-18
---

# The three Golden Rules of salary reconciliation

These are **never violated**. Every other adjustment must be made without breaking them.

## Rule

1. **`Σ REVISED_PF = ECR_PF`** — the salary sheet's PF must equal the EPFO-filed ECR,
   **per employee**, not just in total.
2. **`Σ REVISED_ESIC = Future-sheet ESIC`** — per employee.
3. **NET PAYABLE NEVER CHANGES** — any difference created while fixing PF/ESI/basic is absorbed
   through **OTHER DEDUCTION** (or attendance allowance), so the employee's take-home is
   sacrosanct. See [[net-payable-sacrosanct]].

## Why / basis

The reconciliation exists to make the salary books agree, per employee, with what was actually
filed and deposited with EPFO and ESIC — while never changing what the worker was paid. If net
payable moved, we'd be rewriting history and creating a fresh liability. Instead we rebalance
the internal composition (basic ↑ ⇒ other-deduction ↑) and leave the bottom line fixed.

## Worked example

Raising an employee's revised basic by ₹L to hit a PF/ECR target increases PF by ΔPF. To keep
net payable identical, OTHER DEDUCTION is raised by `L − ΔPF`. Allowances are **not** touched,
because they feed the ESI base — see [[net-payable-sacrosanct]].

## Applied in

- [[40-Workings/2026-07-pf-reconciliation-fy2526]]
- [[40-Workings/2026-07-wage-code-50pct-dec-mar]]
- [[40-Workings/2025-fy2425-maharashtra-pf-esi]]
