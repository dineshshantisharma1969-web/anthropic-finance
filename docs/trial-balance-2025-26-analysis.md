# Trial Balance Review — FY 2025-26 (01/04/2025 to 31/03/2026)

**Entity:** Impressions Services Private Limited
**Primary source:** `tb 25-26 on date 12.06.2025.xlsx` (system export shared 12-06-2026 by account7@impressionsgroup.in; 1,104 GL accounts) — note the filename says "12.06.2025", which appears to be a typo for 12.06.2026
**Secondary source:** `TRIAL BALANCE .pdf` (signed scanned copy dated ~06-04-2026), used for comparison
**Reviewed:** 12 June 2026

---

## 1. Mechanical integrity — all checks PASS

| Check | Result |
|---|---|
| Opening Dr = Cr | ₹2,533,744,633.40 both sides — tallies |
| Period Dr = Cr | ₹33,874,368,457.34 both sides — tallies |
| Closing Dr = Cr | ₹8,188,344,804.69 both sides — tallies |
| Per-row arithmetic (opening ± period = closing), all 1,104 rows | 0 failures |
| Duplicate GL codes / duplicate GL names | None |
| Negative figures / both-side closing balances | None |

The TB is mechanically sound. Everything below is substantive: classification
errors, unposted entries, and stale balances.

> **Report header quirk:** the export header reads *"Financial Year From
> 01/04/2025 To 31/01/2027"* — a 22-month FY configured in the accounting
> system. The period filter itself (01/04/2025–31/03/2026) is correct, but the
> FY master should be fixed.

---

## 2. Critical findings

### 2.1 Suspense account carrying a balance — R3002
**₹102,411.44 Dr** parked in SUSPENSE ACCOUNT (debits posted during the year,
nothing cleared). Must be investigated and brought to nil before finalization.

### 2.2 FY 2025-26 unbilled revenue accrual not yet booked
- Last year's unbilled revenue (₹67,82,60,915) has been **reversed** — the
  reversal sits as a ₹67.83 crore **debit** in revenue head R1001068, and the
  asset `UNBILLED RECEIVABLE` (A2005003008001) is now nil.
- No current-year unbilled revenue has been accrued.
- Consequence: revenue is currently understated by whatever the 31/03/2026
  unbilled work amounts to. The TB presently shows an **implied net loss of
  ₹12.02 crore** (revenue ₹441.93 cr vs expenses ₹453.95 cr) — this figure is
  not meaningful until the unbilled accrual (and other closing entries) are
  posted. If unbilled revenue is at last year's level, the result swings to a
  profit.

### 2.3 ₹79.79 crore credit balance inside the expense group
`SALARY-OTHER DEDUCTIONS` (X2001002002001010) has a **credit closing balance
of ₹797,906,763** — about 18.6% of the gross salary cost of ₹428.77 crore.
Employee recoveries (PF/ESIC employee share, fines, food, advances etc.) are
being netted inside an expense head. This needs:
1. Reconciliation against actual statutory deposits (employee-share PF/ESIC
   recovered must equal amounts deposited — s.36(1)(va) exposure otherwise);
2. Proper regrouping — recoveries that are liabilities/receivables should not
   sit as a P&L credit.

### 2.4 Asset accounts with credit balances (wrong-side balances)
30 asset-side accounts close with credit balances. Material ones:

| Account | Credit balance (₹) | Issue |
|---|---|---|
| A2005001001004001 SA-ADVANCE TO SITE EMPLOYEES | 65,790,468.00 | An *advance* (asset) account ₹6.58 cr in credit — almost certainly unpaid site wages netted here; should be shown as a liability |
| A2003002017 DBS BANK WCDL | 200,000,000.00 | Working-capital demand loan parked under bank (asset) group — is a **borrowing** |
| A2003002019 ICICI WCDL | 100,000,000.00 | Same — borrowing under asset group |
| A2003002021 IDFC FIRST BANK-CC | 48,380,739.72 | Overdrawn CC — book overdraft/borrowing |
| A1001002005004 ASSETS-OFFICE EQUIPMENT | 5,316,389.25 | A **fixed-asset cost account in credit** — impossible; disposals/depreciation posted in excess of cost. FA register needs correction |
| ~25 employee imprest accounts (SI-/SA- series) | 1 — 500,000 each | Employees spent more than imprest given, or postings to wrong ledgers |

### 2.5 Liability accounts with debit balances
| Account | Debit balance (₹) | Issue |
|---|---|---|
| L2008011 LEAVE ENCASHMENT PAYABLE 2025-26 | 13,109,107.25 | Payments exceed provision — FY26 provision entry not yet booked |
| L2007002003003 BONUS PAYABLE-FY-2025-26 | 6,490,193.01 | Same — bonus paid but provision missing |
| L2007002002008 SALARY PAYABLE-OTHER-2025-26 | 6,474,226.00 | Payable overdrawn |
| L2007002002009 SALARY-FULL & FINAL PAYABLE | 4,896,907.00 | F&F paid in excess of amounts booked |
| L2005003 SUNDRY CREDITORS-INSURANCE | 605,101.00 | Creditor in debit — advance or double payment |
| L2004001017/18/19 GST-ANDHRA PRADESH "NOT IN USE" | net 383,273.08 Dr | Accounts marked **NOT IN USE** still carrying balances, untouched all year |
| Small: ESIC PAYABLE DDUGKY (3,057), EPF-DDUGKY (2,880), TDS ON INTEREST-TATA CAPITAL (11,127) | | Excess deposits / mispostings |

### 2.6 Books materially changed after the signed TB
The signed PDF TB (early April 2026) showed period totals of
₹31,530,032,518.67 and closing totals of ₹7,411,143,797.62. This export shows
₹33,874,368,457.34 and ₹8,188,344,804.69 — i.e. roughly **₹2.34 thousand
crore of additional transaction volume** has been posted into FY 2025-26
after the signed copy was produced. Normal during finalization, but the
signed copy in Drive is now stale and should not be circulated.

---

## 3. Stale / old balances needing action

**Old recoverables (₹12+ crore locked up, all dormant):**
| Account | Balance (₹) |
|---|---|
| TDS Receivable 2018-19 | 10,231,149.10 |
| TDS Receivable 2019-20 | 8,323,811.00 |
| Income-tax refund AY 2021-22 | 2,596,360.00 |
| Income-tax refund AY 2023-24 | 44,417,439.00 |
| Income-tax refund AY 2024-25 | 54,480,447.56 |
| TDS on GST receivable 2021-22 (DL/HR/UP/WB etc., several accounts) | ≈ 1,190,000 combined; HP account is **negative ₹2.38** (over-adjusted) |

Reconcile with Form 26AS / GST portal; write off what is irrecoverable.

**Old payables still parked:**
- Salary Payable 2022-23: ₹4,398,098 Cr (untouched)
- Salary Payable 2023-24: ₹4,213,501.80 Cr (untouched)
- Salary Payable 2024-25: ₹14,649,488.83 Cr remaining
- GST Payable 21-22: ₹340,147.76 Cr still unpaid
- Provision for Income Tax FY 2024-25: ₹19,800,000 Cr — should be settled
  against assessment/advance-tax/TDS, not carried

**Other dormant items:** `CASH-WITH IT` ₹5,350,000 (cash with the Income-Tax
department, unchanged — track recovery/adjustment); Deferred Tax Asset
₹29,044,756 untouched (needs FY26 re-measurement); 218 asset accounts in
total carry balances with zero movement all year.

---

## 4. Tax & compliance flags

- **Disallowable expenses booked (quantified):** Interest on TDS on salary
  ₹600 · Interest on ESIC ₹40,555 · Fine & penalty ₹13,783 · ESIC damages
  ₹14,400 · EPF damages ₹29,432 · GST penalty ₹3,624 · GST late fee ₹107,084.
  Small in amount but (a) must be disallowed in the tax computation and
  (b) indicate **delayed statutory deposits** — verify employee-share PF/ESIC
  deposit dates (s.36(1)(va)) given the scale of payroll (₹428.77 cr).
- **OTHER DEDUCTION-PENALTY ₹2,49,92,438 + OTHER DEDUCTION ₹2,54,30,791** —
  ₹5+ crore of client-imposed deductions/penalties expensed. Review nature
  (contractual short-deduction vs penal) for tax treatment and for operational
  follow-up.
- **Cash in hand ₹71,93,488** at year end (up from ₹12.99 lakh) — high
  physical-cash holding; verify denominations/custody and s.40A(3) compliance
  on cash payments.
- **Provision for doubtful debts is a flat ₹1.00 crore** against sundry
  debtors of **₹112.79 crore** (≈93 days of revenue, up ₹10.66 cr during the
  year). An ageing-based ECL/provision estimate is advisable.
- **Director remuneration ₹3.58 crore** — ensure related-party disclosure and
  approval compliance.

---

## 5. Inter-branch & structural items

- Inter-branch/HO accounts in the company's own name still carry debit
  balances: A2006001 ₹24,005,200 · A2006002 ₹23,312,931 · A2006004
  ₹24,056,246.78 · A2006005 ₹13,647,479.55 (total ≈ ₹8.50 crore). A2006003
  was cleared to nil during the year (the ₹0.58 residue in the signed PDF is
  gone). These project/branch control balances (DDU-GKY, BSDM, UPSDM) need
  reconciliation with the respective project books before consolidation.
- `BRANCH TRANSFER` (R1001067) shows ₹13,244,100.37 Dr = Cr, netting to nil —
  acceptable, but confirm branch transfers are excluded from GST turnover
  reconciliations.
- **Parallel duplicate GST ledgers with inconsistent spellings** — `RCM
  DEFFERED-CGST/SGST/IGST` *and* `RCM-DEFERRED PAYABLE-…` both active with
  offsetting balances (±₹8,587 etc.); `TDS ON GST RECIEVABLE` misspelt.
  Merge and standardize.
- Fixed assets fragmented by GST rate (`ASSETS TELEVISION-18%`/`-28%`,
  `RENT` vs `RENT-18%`, etc.) — complicates the FA register and depreciation
  blocks.
- `SHORT & EXCESS` (X2001003011005018) net **credit ₹12,573.15** — cash/books
  differences being absorbed in P&L rather than investigated.
- GST closing positions to reconcile with portal: GST Payable 25-26
  ₹8,24,61,844 Cr; `GST PAYABLE.` ₹47,67,957 Cr (unlabelled-year account);
  input ledgers CGST ₹2.31 lakh / SGST ₹20.01 lakh / IGST ₹0.17 lakh Dr —
  note the odd CGST-vs-SGST asymmetry (these normally move in tandem);
  reconcile with GSTR-3B/2B and the electronic credit ledger.

---

## 6. Recommended actions (priority order)

1. Post the **FY26 closing entries**: unbilled revenue accrual, bonus / leave
   / gratuity provisions (several 2025-26 provision accounts are overdrawn),
   then re-run the TB — the current ₹12 crore loss is not a final picture.
2. Clear **suspense ₹1,02,411.44** to nil with documentation.
3. Regroup borrowings: move **WCDL ₹30 cr + overdrawn IDFC CC ₹4.84 cr** out
   of bank-asset grouping into borrowings.
4. Investigate the **₹6.58 cr credit in SA-Advance to Site Employees** and the
   **credit balance in Assets-Office Equipment**; correct classifications.
5. Reconcile **Salary-Other Deductions ₹79.79 cr** with statutory deposits
   and regroup.
6. Action old TDS/IT-refund recoverables and prior-year salary/GST payables
   (write-off / pay / reverse with approvals).
7. Reconcile all GST ledgers with the portal; merge duplicate RCM ledgers;
   nil and block the "NOT IN USE" Andhra Pradesh accounts.
8. Review the flat ₹1 cr doubtful-debt provision against a debtor ageing.
9. Quantify disallowances (penalties/damages/late fees) in the tax
   computation; verify PF/ESIC employee-share deposit timeliness.
10. Housekeeping: settle and close the 218 dormant asset ledgers and
    overdrawn employee imprest accounts; fix the 22-month FY master in the
    accounting system.

---

*Appendix — earlier scanned-PDF review:* the signed `TRIAL BALANCE .pdf`
(April 2026) was analysed first via OCR; its grand totals also tallied and the
same structural issues (suspense, A2006xxx, old recoverables) were visible.
All figures in this report are taken from the 12-06-2026 Excel export, which
supersedes it.
