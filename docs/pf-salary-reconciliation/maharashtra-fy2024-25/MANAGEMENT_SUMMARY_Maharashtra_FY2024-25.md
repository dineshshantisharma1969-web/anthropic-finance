# Maharashtra (AISSS) — PF Reconciliation FY2024-25
## Management Summary — for finalisation & sign-off

**Prepared:** 2026-07-08 · **Scope:** Maharashtra branch, Apr-24 → Mar-25 · **Basis:** salary sheet vs
EPFO-filed ECR (West challan + DMART), West-only.

---

## 1. Headline

| | |
|---|---|
| Employee-months reconciled | **21,551** (~1,750/month, 6 Maharashtra branches) |
| Reconciliation outcome | **PF fully reconciled — ₹0 gap on every month; all statutory checks pass** |
| Net Payable impact | **₹0** — no employee's net pay changes (differences parked in Other Deduction) |

## 2. The numbers (year)

| Line | ₹ |
|---|--:|
| Original salary PF (employee EE) | 3,25,22,667 |
| ECR PF filed (West + DMART) | 3,06,22,338 |
| **Reconciled / Revised PF (= ECR, capped at ₹1,800)** | **3,02,29,684** |
| PF gap after reconciliation | **0** |
| PF parked in Other Deduction (net-neutral) | 22,92,983 |

## 3. Sign-off checklist (all ✅)

- ✅ **Σ Revised PF = ECR** per employee (₹0 gap, all 12 months)
- ✅ **Net Payable unchanged** on every row
- ✅ **PF = 12% of Basic+DA**, PF ≤ ₹1,800, Basic+DA ≤ ₹15,000 (0 violations)
- ✅ **West-only ECR** — verified Apr/Oct/Jan vs raw challan: 0 South leakage
- ✅ **ESI reconciliation — DONE** — filed ESIC ₹1,08,11,638 (emp 0.75% ₹20,34,384 + employer 3.25% ₹87,77,254) validated; West-only; see item C

## 4. Items needing a management decision

| # | Item | ₹ / count | Decision needed |
|---|---|--:|---|
| **A** | **Employees below ₹15,000/month, full attendance, NOT in ECR** — potential PF-coverage shortfall (they arguably should be in PF but weren't filed) | **332 emp-months** · PF ₹5,14,086 | Review — regularise in ECR, or confirm exempt? See `Coverage_Gap_Book`. |
| **B** | **ECR filed above the ₹1,800 statutory EE cap** — capped in the reconciliation; surplus not filed as EE PF | ₹3,57,385 (991 emp-months) | Note/accept as reconciling item |
| **C** | **ESI coverage gaps** — salary employees with gross ≤ ₹21,000 (ESI-eligible) **not in the filed ESIC register** | **750 emp-months** | Review — regularise in ESI, or confirm exempt? See `esi/ESI_COVERAGE_GAPS_YEAR.csv` |
| **D** | **ESI above ₹21,000 ceiling** (contribution-period continuation — generally legitimate) | 690 rows | Confirm as period-continuation |

### ESI position (filed / deposited)

| Line | ₹ |
|---|--:|
| ESIC wages | 27,00,69,345 |
| ESI employee (0.75%) | 20,34,384 |
| ESI employer (3.25%) | 87,77,254 |
| **ESI total deposited** | **1,08,11,638** |

ESI employee 0.75% and employer 3.25% hold on every row (bar 2 rounding cases ≤ ₹1.5); register is
100% Maharashtra (West-only). Full ESI checks: `esi/CHECKS_AND_BALANCES_ESI_Maharashtra_FY2024-25.md`.

## 5. What backs this up (files)

- `Maharashtra_PF_Summary_FY2024-25.xlsx` — one-page month-wise summary + reconciliation bridge + rule stats + checks status
- `Maharashtra_PF_Coverage_Gap_Book_FY2024-25.xlsx` — the 332 coverage-gap employees (item A), line by line
- `corrected_monthly/CORRECTED_<MONTH>.csv` — the 12 corrected monthly sheets (per employee)
- `CHECKS_AND_BALANCES_Maharashtra_FY2024-25.md` — full checks report

*PF reconciliation only. Figures are final for PF; ESI is the one open workstream (item C).*
