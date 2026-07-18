---
type: rule
domain: pf
ref: m13-annual-trueup
title: M13 annual true-up rule
effective_from: 2025-04-01
effective_to:
status: active
supersedes:
superseded_by:
source: PF_SALARY_RECONCILIATION_SKILL_v4 · SALARY_KNOWLEDGEBASE.md §4
based_on: "[[pf-contribution-basis]]"
tags: [pf, m13, annual, trueup]
created: 2026-07-18
---

# M13 annual true-up rule

## Rule

M13 ("13th-month") is the **annual true-up** that reconciles the full year's PF against the
filed ECR, per employee, holding GROSS / PF / NET:

- PF = **12% on BASIC+DA**.
- **ECR > 0** → `REVISED_BASIC = ECR / 0.12 − DA`; any plug goes to **attendance allowance**.
- **ECR = 0** → project the employee above ₹15,000 by **reducing days first**, then lifting
  basic, so PF falls to zero (mirrors [[pf-ecr-case-rules|Not-in-ECR]]).
- GROSS, PF and NET are all held.

## Why / basis

Monthly runs can drift slightly from the year's filed ECR; M13 trues the whole year to the ECR
in one pass so the annual books match EPFO exactly, without disturbing gross or net.

## Applied in

- [[40-Workings/2026-07-pf-reconciliation-fy2526]]
- [[40-Workings/2026-07-pivot-consol-live-linked]]
