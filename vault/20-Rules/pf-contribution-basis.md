---
type: rule
domain: pf
ref: pf-contribution-basis
title: PF contribution basis — 12% of BASIC+DA, ₹15,000 ceiling
effective_from: 2025-04-01
effective_to:
status: active
supersedes:
superseded_by:
source: EPF Scheme · PF_SALARY_RECONCILIATION_SKILL_v4
based_on: "[[10-Law/PF-ESI/README]]"
tags: [pf, epf, ceiling]
created: 2026-07-18
---

# PF contribution basis — 12% of BASIC+DA, ₹15,000 ceiling

## Rule

- Employee PF = **12% of (BASIC + DA)**.
- PF wages are **capped at ₹15,000/month** → maximum employee PF = **₹1,800/month**.
- Above ₹15,000 of BASIC+DA, **no additional PF** is due (this is why the
  [[pf-ecr-case-rules|Not-in-ECR]] rule sets BASIC = ₹15,001 to zero out PF).
- Enforced as a post-pass: `REVISED_PF = 12% × (BASIC+DA)`, reducing days if needed, integer days.

## Why / basis

Statutory EPF contribution rate and wage ceiling. The employer matches 12% (of which a portion
goes to EPS), but the reconciliation tracks the **employee (EE)** leg against the ECR.

## Worked example

BASIC+DA = ₹12,000 → PF = ₹1,440. BASIC+DA = ₹20,000 → PF capped at ₹1,800 (12% × ₹15,000),
not ₹2,400.

## Applied in

- [[40-Workings/2026-07-wage-code-50pct-dec-mar]]
- [[40-Workings/2026-07-pf-reconciliation-fy2526]]
