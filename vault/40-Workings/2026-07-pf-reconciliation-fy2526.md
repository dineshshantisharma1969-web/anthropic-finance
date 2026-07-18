---
type: working
domain: pf
ref: pf-reconciliation-fy2526
title: PF reconciliation FY2025-26 (M13 final)
period: FY2025-26
run_date: 2026-07-17
status: final
result_headline: Reconciled PAN PF 29,06,52,769 = ECR filed, gap 0
tags: [pf, ecr, reconciliation, m13, fy2526]
created: 2026-07-18
---

# PF reconciliation FY2025-26 (M13 final)

## Question

Reconcile the full-year salary PF, per employee, against the filed ECR — and true it up via
M13 — holding net payable.

## Method

Applied [[pf-ecr-case-rules]] (Case A/B/Cond 2/Not-in-ECR), [[pf-contribution-basis]] (12%,
₹15k ceiling), and [[m13-annual-trueup]]; net held via [[net-payable-sacrosanct]].

## Result

| Anchor | ₹ |
|---|--:|
| Net Payable (sacrosanct, drift 0) | **2,93,29,71,946** |
| Reconciled PAN PF (= ECR filed, gap 0) | **29,06,52,769** |
| Back-office PF | 1,64,19,591 |
| Booked PF (PAN + back-office) | 30,70,72,360 |
| Tally EPF-Employee payable ledger | 29,67,46,845 |
| Future-basis ESI (statutory anchor) | 1,86,93,848 |
| Professional Tax | 84,33,198 |

Per-employee equality verified 13-Jul-2026: every salary-sheet employee's REVISED_PF = his
filed ECR EE, all 12 months. Checks report: **7 PASS · 5 REVIEW · 0 FAIL**.

## Sources & artefacts

- Repo: `docs/pf-salary-reconciliation/CHECKS_AND_BALANCES_FY2025-26.md`, `SUMMARY_FY2025-26.csv`,
  `dashboard.html`.
- Drive: `CORRECTED SALARY 25-26 (M13 FINAL)` (`1PU9QyY4VwyNrlHzwaBJj8Sku0qKmhmky`), `ECR PF 2025-26`
  (`1YsX0QjjOSRYrhkFDPrEl95oJBQN1Thsp`).
- Full year live tie-out: [[2026-07-pivot-consol-live-linked]].

## Open items

- Documented review items only (see KB §5): Oct net vs pivot ₹9,76,861 (use pivot); Jun PF
  ₹858 (use pivot/ECR); Jan/Feb gross ≈ 2× (verify before statutory use).
