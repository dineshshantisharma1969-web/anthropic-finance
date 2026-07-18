---
type: working
domain: salary
ref: wage-code-50pct-dec-mar
title: Wage-code 50% check & fix, Dec-25 → Mar-26 (V2 sheets)
period: Dec-2025 → Mar-2026
run_date: 2026-07-18
status: final
result_headline: 1,874 true violators; fixed net-neutral; PF liability +~₹6.2L vs ₹1.67 Cr naive
tags: [wage-code, salary, basic, pf, restructuring]
created: 2026-07-18
---

# Wage-code 50% check & fix, Dec-25 → Mar-26 (V2 sheets)

## Question

Apply the [[wage-code-50pct-rule]] to the Dec–Mar V2 monthly salary files: find employees whose
BASIC+DA is below 50% of gross, and restructure them net-neutrally.

## Method

- Applied [[wage-code-50pct-rule]]: **gross (remuneration) basis**, day-rated employees'
  per-day basic × **calendar days in month** (Dec 31, Jan 31, Feb 28, Mar 31).
- Fixed with an **inner goal-seek loop** (moving target — gross rises with basic): raise basic
  until basic+DA = 50% of final gross.
- Held net payable via OTHER DEDUCTION; allowances untouched (ESI base preserved) —
  [[net-payable-sacrosanct]]. PF at 12%/₹15k ceiling — [[pf-contribution-basis]].
- Delivered a management-presentable `50PCT_WAGE_CODE_WORKING` tab (RAW vs RESTRUCTURED vs NET
  EFFECT, per employee) in each month's file.

## Result

- Raw CTC-basis flagged **11,662** employee-months. After correct **day-rate conversion + gross
  basis**, true violators = **1,874**: Dec 457 · Jan 467 · Feb 447 · Mar 503.
- Fix impact (4 months): basic lift **₹1.18 Cr**; PF EE increase **₹2,96,548** (capped); OTHER
  DEDUCTION increase **₹1.15 Cr**; **net change 0 for every employee**; all fixed rows land at
  exactly **50.00%**.
- **PF liability increase ≈ ₹6.2 L (EE+ER) over 4 months**, vs **≈ ₹1.67 Cr** under a naive
  (no day-rate, CTC-basis) restructuring — about **96% saved** by the correct basis.

## Sources & artefacts

- Drive `M13_FINAL_EXTRACTED`: `<Month>_V2_50pct_CTC_{ALL,VIOLATIONS}.csv`, `_50PCT_*` outputs;
  `50PCT_WAGE_CODE_WORKING` tab in each Dec–Mar `_withDays` Google Sheet.
- Repo: `docs/pf-salary-reconciliation/wage-code-50pct/`.

## Open items

- **Restructuring decision** — whether to apply the fix to the live salary files is a
  management call (KB §5 item 11). The workings and net-neutral method are ready.
