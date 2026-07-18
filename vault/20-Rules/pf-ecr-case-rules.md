---
type: rule
domain: pf
ref: pf-case-rules
title: PF adjustment rules — Case A, Case B, Cond 2, Not-in-ECR
effective_from: 2025-04-01
effective_to:
status: active
supersedes:
superseded_by:
source: PF_SALARY_RECONCILIATION_SKILL_v4 · SALARY_KNOWLEDGEBASE.md §4
based_on: "[[10-Law/PF-ESI/README]]"
tags: [pf, ecr, salary, reconciliation]
created: 2026-07-18
---

# PF adjustment rules — Case A, Case B, Cond 2, Not-in-ECR

The four rules that align each salary row's PF to the filed ECR, per employee, while holding
net payable (see [[pf-golden-rules]]).

## Rule

Compare the salary sheet's employee PF against the filed **ECR** PF for the same employee:

| Case | Condition | Action |
|---|---|---|
| **Case B** | ECR < salary PF **and** fixed BASIC+DA ≤ ₹15,000 | Back-calculate **days** so PF falls to the ECR figure |
| **Case A** | ECR < salary PF **and** BASIC+DA > ₹15,000 | Park the difference in **OTHER DEDUCTION** (net held) |
| **Cond 2** | ECR > salary PF | OTHER DEDUCTION goes **down** to absorb the extra PF |
| **Not-in-ECR** | employee absent from the ECR | Set BASIC = ₹15,001, **PF = 0** (pushed just above the ₹15k ceiling so no PF is due) |

**Multi-site employees:** an employee can appear on several salary rows (different sites) but PF
is filed once. The **main (anchor)** row is matched to the ECR; **secondary** rows are zeroed
(`PF_SECONDARY`), left otherwise untouched.

## Why / basis

PF is a per-employee statutory liability filed via the ECR. The salary book must mirror exactly
what was filed — no more, no less — so any gap is either corrected at source (days/basic) or
parked net-neutral in OTHER DEDUCTION. The ₹15,000 wage ceiling (PF payable on max ₹15,000 of
BASIC+DA) is what makes the Not-in-ECR ₹15,001 trick valid: above the ceiling, no PF is due.

## Worked example

Employee with salary PF ₹2,100 but ECR EE ₹1,800, BASIC+DA ₹18,000 (> ₹15k) → **Case A**: the
₹300 gap is parked into OTHER DEDUCTION; days and basic stay; net payable unchanged.

## Applied in

- [[40-Workings/2026-07-pf-reconciliation-fy2526]]
- [[40-Workings/2025-fy2425-maharashtra-pf-esi]]
- [[40-Workings/2026-04-april-reconciliation]]
