# Trial Balance Comparison — FY 2025-26

**Entity:** Impressions Services Private Limited
**Files compared (period 01-Apr-2025 to 31-Mar-2026):**

| Side | File | Source |
|------|------|--------|
| Anuj (latest) | `BS _TB _2025-26 ver 1.1_12062026.xlsx` → sheet **`Trail Maxus 25-26`** | shared by Anuj on 15-Jun-2026 |
| Mine | `tb on 31.3.2026.xlsx` → sheet `Report639163396048560599` | dinesh@ (own working TB) |

Both trial balances carry the **same 1,106 GL accounts** — no account exists on one side only.
**72 accounts have different closing balances.** All figures below are **net closing (Dr − Cr)**; "diff" = Anuj − Mine. ₹ Cr = ₹ crore.

> Integrity note: my TB balances to **0**. Anuj's `Trail Maxus` sheet is **out of balance by +₹1.17 Cr** — this equals the RTD/Flexi branch balances he has pulled into the sheet (see §3); they net off in his consolidated group statements. A stray `GRAND TOTAL` text row (₹1.17 Cr) in his sheet was excluded.

---

## 1. Headline impact

| Measure | Effect of Anuj's TB vs mine |
|---|---|
| **Profit before tax** | **≈ ₹12.80 Cr HIGHER** in Anuj's version (total expenses ₹12.80 Cr lower) |
| **Reported turnover / revenue** | **₹47.51 Cr HIGHER on the face of P&L** — but this is presentation only; actual gross receipts are identical (see §2) |
| **Balance sheet** | Grossed-up: a new ₹47.51 Cr unbilled-receivable asset, salary payable cut ₹19.08 Cr, employee advances cut ₹5.85 Cr, RTD/Flexi branches (₹1.17 Cr) consolidated in |
| **Net worth (real)** | Changes only by the genuine ₹12.80 Cr expense difference — the rest are reclassifications |

The 72 differences fall into **three buckets**: (2) pure reclassifications, (3) real P&L differences, (4) balance-sheet restatements.

---

## 2. Reclassifications — NO effect on profit or net worth (presentation only)

### 2a. Unbilled — ₹47.51 Cr moved from revenue to a balance-sheet asset
| Account | Mine | Anuj | Diff |
|---|--:|--:|--:|
| `R1001068` UNBILLED REVENUE (netted in *Receipts from operations*) | 67.83 | 20.32 | −47.51 |
| `A2005003008001` UNBILLED RECEIVABLE (current asset) | 0.00 | 47.51 | +47.51 |
| **Combined unbilled** | **67.83** | **67.83** | **0.00** |

- You netted the full ₹67.83 Cr of unbilled against *Receipts from operations*. Anuj kept only ₹20.32 Cr netted and **carved out ₹47.51 Cr as a separate "Unbilled Receivable" current asset**.
- Effect: his **P&L shows revenue ₹47.51 Cr higher** and his **balance-sheet current assets ₹47.51 Cr higher**. **Actual gross receipts are identical at ₹508.76 Cr** on both sides; **profit and net worth are unchanged.** This is the cleaner Ind-AS / Schedule III presentation (contract asset shown gross).

### 2b. Small offsetting swaps (net zero)
RCM-deferred SGST/IGST pairs, CGST/SGST input pairs, employee-advance code swaps (e.g. Randhir Verma), Cash ↔ employee advance ₹6,986 — each moves between two codes with no net impact.

---

## 3. Real Profit & Loss differences — total expenses ₹12.80 Cr LOWER in Anuj → PBT ₹12.80 Cr HIGHER

The driver is **employee costs**. Anuj has booked salary on a **gross basis with larger deductions**, and trimmed bonus / leave encashment:

| Account | Mine (₹Cr) | Anuj (₹Cr) | Diff (₹Cr) | Effect on profit |
|---|--:|--:|--:|---|
| `X2001002002001003` SALARY ACCOUNT | 360.85 | 428.77 | **+67.92** | expense ↑ |
| `X2001002002001010` SALARY-OTHER DEDUCTIONS (contra) | −3.49 | −79.79 | **−76.30** | expense ↓ |
| `X2001002002001007` LEAVE ENCASHMENT | 4.87 | 0.60 | **−4.27** | expense ↓ |
| `X2001002002001004` BONUS | 4.40 | 1.47 | **−2.93** | expense ↓ |
| `X2001003011004003` FOODING DEDUCTION | −0.29 | 2.29 | **+2.58** | expense ↑ |
| **Net employee benefit expense** | **410.77** | **395.19** | **−15.58** | **profit ↑ ₹15.58 Cr** |

Partly offset by small increases elsewhere: Site Expense +₹0.54 Cr, Insurance +₹0.54 Cr, Travelling/Conveyance +₹0.26 Cr, Misc +₹0.19 Cr, Purchases +₹0.18 Cr, Discount/Other deduction/Repairs/Fees ≈ +₹0.47 Cr.

**Net of everything: expenses ₹12.80 Cr lower in Anuj's TB → pre-tax profit ₹12.80 Cr higher.**

> ⚠️ Decide whose treatment is correct **before finalising** — a ₹12.80 Cr profit swing is material. The whole difference is concentrated in the salary / deductions / bonus / leave-encashment block, so reconcile the payroll accrual with Anuj.

---

## 4. Balance-sheet restatements (the counter-entries to §3 plus consolidation)

| Account | Mine (₹Cr) | Anuj (₹Cr) | Diff (₹Cr) | Meaning |
|---|--:|--:|--:|---|
| `L2007002002007` SALARY PAYABLE 2025-26 | −28.50 | −9.42 | +19.08 | liability **cut ₹19.08 Cr** |
| `A2005001001004001` ADVANCE TO SITE EMPLOYEES | −0.73 | −6.58 | −5.85 | net advance **down ₹5.85 Cr** |
| `A2005004004` ISPL RTD CURRENT ASSETS | 0.00 | 0.92 | +0.92 | RTD branch pulled in |
| `A1001002009` ISPL-FLEXI ASSETS | 0.00 | 0.16 | +0.16 | Flexi branch pulled in |
| `A2005001002005002` STAFF IMPREST – GOVT (BSDM) | 0.00 | 0.09 | +0.09 | new |
| `A1001002008` ISPL RTD ASSETS | 0.00 | 0.01 | +0.01 | RTD branch pulled in |
| `L2004005001` PROFESSIONAL TAX PAYABLE | −0.42 | −5.09 | −4.67 | liability **up ₹4.67 Cr** |
| `A2002001` SUNDRY DEBTORS CONTROL | 1,129.89 | 1,127.77 | −0.21 | debtors trimmed ₹0.21 Cr |
| `L2007001002` STAFF WELFARE FUND COLLECTED | −2.08 | −0.35 | +0.17 | liability cut |
| `A2004006056` TDS RECEIVABLE 2025-26 | 9.49 | 9.65 | +0.16 | + small TDS/prepaid items |

The salary-payable cut (₹19.08 Cr) and employee-advance reduction (₹5.85 Cr) are the **balance-sheet side of the payroll re-statement** in §3. The RTD/Flexi/Govt-imprest lines (≈₹1.17 Cr) are **branch balances Anuj has consolidated** that were nil in my TB — this is also why his Maxus sheet is out of balance by ₹1.17 Cr on its own.

---

## 5. What to do next
1. **Resolve the payroll block** (salary gross-up, deductions, bonus, leave encashment) — this alone is the ₹12.80 Cr PBT difference. Agree one basis with Anuj.
2. **Adopt the unbilled split** (₹47.51 Cr to Unbilled Receivable) if presenting per Schedule III — it is profit/net-worth neutral but improves disclosure.
3. **Confirm RTD/Flexi consolidation** is intended in this entity and that the ₹1.17 Cr is eliminated correctly so the final TB balances.
4. Clean up the stray `GRAND TOTAL` text row in Anuj's `Trail Maxus 25-26` sheet.

*Generated from a GL-by-GL reconciliation of the two trial balances; groupings use your own "Grouped TB 25-26 (Adjusted)" mapping.*
