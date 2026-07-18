---
type: working
domain: salary
ref: pivot-consol-live-linked
title: FY2025-26 live-linked pivot workbook (consol + PF tie-out)
period: FY2025-26 (Apr-25 → Mar-26)
run_date: 2026-07-18
status: final
result_headline: FY NET PAYABLE 2,93,29,71,946 — pivots tie to the rupee
tags: [salary, pivot, consol, pf, netpayable, google-sheets]
created: 2026-07-18
---

# FY2025-26 live-linked pivot workbook (consol + PF tie-out)

## Question

Build a **live, formula-linked** pivot summary of the full-year consol (like the attached
`PIVOT_FY202526_linked.xlsx`) that management can read, and that recalculates when the data
changes — plus PF tie-out and reconciliation tabs.

## Method

- Server-side (n8n + Drive/Sheets API, one-shot manual runs — no schedules) converted
  `CONSOL_FY202526_RevisedBlock_REBUILT.xlsx` to a native Google Sheet.
- Added tabs with **live SUMIFS/COUNTIFS** formulas pointing at the data sheet:
  `Pivot_Month`, `Pivot_State_NetPayable`, `PF_Tieout`, `PF_Reco_Summary`, `README`.
- **Correction made:** the rebuilt consol had dropped **35 April rows worth ₹1,95,642**.
  Diffed April employee-by-employee (EMPCODE+SITECODE) against the older consol, appended the
  missing rows, re-verified.

## Result

Read back **live** from the sheet after writing:

| Check | Value |
|---|--:|
| Rows | 235,077 (April 19,161 ✓) |
| FY REVISED_NET_PAYABLE (`Pivot_Month`) | **2,93,29,71,946** |
| State pivot GRAND TOTAL | **2,93,29,71,946** (ties to month pivot to the rupee) |
| FY ECR_PF | 29,17,54,961 |
| `PF_Tieout` CHECK columns (all 12 months) | **0** (salary PF = ECR EE = ANUJ register) |
| Golden rule | REVISED_NET_PAYABLE == NETPAYABLE every row ([[pf-golden-rules]]) |

PF tie-out totals: ECR EE incl. back office ₹29,55,70,456; with arrears/penalties (ANUJ month
total) ₹29,67,77,682.

## Sources & artefacts

- Live sheet **`PIVOT_FY202526_LIVE_LINKED`** in Drive folder `M13_FINAL_EXTRACTED`
  (`1848k7zbPRPRlsp3G9iK_6CG6Ldgs9tV3`).
- Data tab `CONSOL_RevisedBlock`; source `CONSOL_FY202526_RevisedBlock_REBUILT.xlsx`.
- n8n workflows (one-shot): pivot build, PF tabs, April-row restore, verify.

## Open items

- None. Pivots tie out; temp working copy trashed.
