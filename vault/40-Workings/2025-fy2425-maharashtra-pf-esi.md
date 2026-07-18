---
type: working
domain: pf
ref: fy2425-maharashtra-pf-esi
title: Maharashtra (AISSS) FY2024-25 PF + ESI reconciliation
period: FY2024-25 (Maharashtra / West-only)
run_date: 2026-07-17
status: final
result_headline: REVISED_PF 3,02,29,684 = ECR (gap 0); ESI filed 1,08,11,638
tags: [pf, esi, maharashtra, aisss, fy2425]
created: 2026-07-18
---

# Maharashtra (AISSS) FY2024-25 PF + ESI reconciliation

## Question

Reconcile 12 months of Maharashtra (West-only) salary PF against the filed ECR, and validate
the filed ESIC register.

## Method

[[pf-ecr-case-rules]] with ECR capped at the ₹1,800 statutory EE cap ([[pf-contribution-basis]]);
West-only isolation (no South leakage); net held ([[net-payable-sacrosanct]]).

## Result

**PF (all checks 0):**

| Anchor | ₹ |
|---|--:|
| REVISED_PF = ECR_PF_CAPPED, gap 0, 21,551/21,551 rows exact | **3,02,29,684** |
| Original salary PF (EE) | 3,25,22,667 |
| ECR PF filed (West + DMART) | 3,06,22,338 |
| Above-₹1,800 cap surplus (documented, not filed) | 3,57,385 |
| PF parked in OTHER DEDUCTION (net-neutral) | 22,92,983 |

**ESI (filed register, West-only):** ESIC wages ₹27,00,69,345; EE @0.75% **₹20,34,384**; ER
@3.25% ₹87,77,254; **total deposited ₹1,08,11,638**. 0.75%/3.25%/West-only checks pass.

## Sources & artefacts

- Repo: `docs/pf-salary-reconciliation/maharashtra-fy2024-25/` (checks, corrected monthly CSVs,
  combined xlsx, builder).
- Drive: `MAHARASHTRA ASSSIS DATA 24-25` (`13Q9wUiqy4UMwc-0VWi8EEtF3fDSbC2wc`).

## Open items

- **750 ESI coverage gaps** (gross ≤ ₹21k, not filed) + 690 above-ceiling (period continuation).
- Row-level salary-ESI edits (E1–E4) need the full salary sheet run locally.
