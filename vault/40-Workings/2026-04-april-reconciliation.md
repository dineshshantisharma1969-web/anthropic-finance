---
type: working
domain: pf
ref: april-2026-reconciliation
title: April 2026 PF/ESI reconciliation (M12/M15 final)
period: April 2026 (FY2026-27)
run_date: 2026-07-17
status: final
result_headline: REVISED_PF 2,52,21,042 = ECR (gap 0); 4,974 action rows open
tags: [pf, esi, april2026, fy2627, reconciliation]
created: 2026-07-18
---

# April 2026 PF/ESI reconciliation (M12/M15 final)

## Question

Reconcile the April-2026 salary sheet (21,152 rows) against the filed ECR, per employee.

## Method

[[pf-ecr-case-rules]] + [[pf-contribution-basis]]; footed row-by-row from the full sheet; net
held ([[net-payable-sacrosanct]]).

## Result

| Anchor | ₹ |
|---|--:|
| REVISED_PF = ECR_PF, gap 0, 21,152/21,152 rows exact | **2,52,21,042** |
| NETPAYABLE = REVISED_NET (drift 0) | **25,99,37,250** |
| GROSS AMT / REVISED_GROSS | 30,72,93,356 / 35,71,24,660 |
| PT | 7,23,250 |

Rule mix: PF_ANCHOR 18,389 · PF_SECONDARY 1,403 · ESI_ONLY 463 · NO_PF_NO_ESI 506 ·
SKIP_ZERO_BASIC 391. Checks: 5 PASS · 1 REVIEW.

## Sources & artefacts

- Repo: `docs/pf-salary-reconciliation/april-2026/` (checks, dashboard, ACTION_NEEDED csv).
- Drive: `SALARY DATA 2026-27` (`1JkGyC90rOMhTLAbd5LqutdzMz-FKD3Ae`).

## Open items

- 🔴 **4,974 ACTION_NEEDED rows, ₹5.45 Cr excess salary** — top reasons: paid above fixed rate
  (2,458), ESI-exempt but rate ≤ ₹21k (1,940), implied full-month ≫ rate (319), low attendance
  (257). List: `april-2026/ACTION_NEEDED_April2026.csv`. **Needs decision.**
- April ESI vs Future gap ₹37,736 (secondary-site / Future-only) — verify before ESI filing.
