# Anuj's TB / Financials FY 2025-26 — Error Review & True Picture

**File:** `BS _TB _2025-26 ver 1.1_12062026.xlsx` (Anuj). Sheets reviewed: `Trail Maxus 25-26`, `flexi 25-26`, `RTD TB`, `BS`, `PL`, `SOCIE`.

## The premise is back-to-front
You asked: *"his trial balance is not matching, how come the balance sheet is matching?"*
**It isn't.** The FY 2025-26 Balance Sheet does **not** tie either — it is **out by ₹90.08 Cr**. Only the **comparative (FY24 & FY25) columns** balance (those are locked/audited). The **current-year column is unbalanced**, so the statements only *look* finished.

| Statement | FY 2025-26 | Ties? |
|---|---|---|
| Trial Balance (`Trail Maxus 25-26`) | DR ₹820.02 Cr vs CR ₹818.85 Cr | ❌ off by **₹1.17 Cr** |
| Balance Sheet (`BS`) | Assets ₹303.16 Cr vs Equity+Liab ₹213.07 Cr | ❌ off by **₹90.08 Cr** |
| FY24 / FY25 BS columns | — | ✅ tie |

---

## Error A — Trial balance out by ₹1.17 Cr: Flexi & RTD assets added with no credit
`Trail Maxus 25-26` totals (his own GRAND TOTAL row): **DR 8,200,238,044.71 − CR 8,188,492,787.71 = +11,745,257**.

That excess debit equals, to the rupee, the branch **assets** he pulled in that were **nil in your TB**:

| GL | Account | Amount (₹) |
|---|---|--:|
| A2005004004 | ISPL RTD CURRENT ASSETS | 91,64,062 |
| A1001002009 | ISPL-FLEXI ASSETS | 15,86,031 |
| A2005001002005002 | STAFF IMPREST – GOVT (BSDM-Bihar-RTD) | 9,20,448 |
| A1001002008 | ISPL RTD ASSETS | 74,716 |
| **Total** | | **1,17,45,257** |

**Mistake:** the Flexi and RTD branch balances were imported on the **debit (asset) side only**. The matching credits — the branches' liabilities / reserves / the inter-unit payable — were **not** brought in. A branch consolidation must bring **both sides**; importing one side throws the TB out by exactly the value imported. (His inter-unit accounts A2006004/A2006005 moved only ₹3 lakh, nowhere near enough to offset.)

---

## Error B — Reserves & Surplus roll-forward is wrong (`SOCIE`)
The Statement of Changes in Equity books the **current-year profit as ₹128.73 Cr** — which is simply a **copy of the opening reserve**, not the actual profit.

```
As at 31 March 2025 (opening)      12,873.31 lakh  = ₹128.73 Cr   ✓
Profit for the period (FY26)       12,873.31 lakh  = ₹128.73 Cr   ✗  (should be ₹35.52 Cr)
As at 31 March 2026 (closing)      25,746.62 lakh  = ₹257.47 Cr   ✗  (opening simply doubled)
```
Actual FY26 profit per his own P&L = **₹35.52 Cr**. Correct closing reserves = 128.73 + 35.52 = **₹164.25 Cr**.

## Error C — Balance Sheet and SOCIE disagree on Reserves
- `BS` shows FY26 Reserves & Surplus = **₹128.73 Cr** — i.e. **frozen at the FY25 figure; current-year profit not added at all.**
- `SOCIE` shows **₹257.47 Cr**.
- Correct = **₹164.25 Cr**.

Three different numbers for the same line. The BS used the "profit-not-transferred" version, which is why equity is understated.

---

## Error D — FY26 Balance Sheet doesn't balance by ₹90.08 Cr
| | ₹ Cr |
|---|--:|
| Total Assets | 303.16 |
| Total Equity & Liabilities (reserves frozen) | 213.07 |
| **Gap (assets unsupported)** | **90.08** |

Decomposition:
- **₹35.52 Cr** = current-year profit never transferred to reserves (Errors B/C).
- **≈ ₹54.57 Cr** = residual **asset overstatement** still unsupported even after adding profit. This is the asset side being grossed up without matching credits — chiefly the **₹47.51 Cr unbilled "receivable" carved out** of revenue (booked as an asset while the revenue was not carried through to reserves), the **₹1.17 Cr Flexi/RTD** branch assets (Error A), plus smaller mapping gaps.

So the BS is not a balanced statement — it is assets ₹303 Cr propped against claims of only ₹213 Cr.

## Error E — No tax provided for FY26
`PL`: Current Tax = **0**, Deferred Tax = **0** on a PBT of **₹35.52 Cr**. Tax provision is missing entirely, so even the ₹35.52 Cr "profit" is pre-tax and overstated.

## Error F — Zero depreciation charged in FY26
`PL` Depreciation & amortization: FY26 = **0** (FY25 = ₹2.60 Cr), while PPE in the BS rose from ₹17.53 Cr to ₹33.16 Cr. Charging a full year's depreciation is missing — this overstates both PPE and profit (symmetrically, so it does not by itself explain the gap, but both PPE and profit are wrong).

---

## True picture of Anuj's FY26 trial balance / financials
1. **The TB does not tie** — short ₹1.17 Cr on the credit side because Flexi/RTD branch assets were imported one-sided.
2. **The BS does not tie** — assets exceed equity+liabilities by ₹90.08 Cr.
3. **Reserves are stated three different ways** (₹128.73 / ₹164.25 / ₹257.47 Cr); only ₹164.25 Cr is correct.
4. **No tax and no depreciation** booked for the year → reported PBT of ₹35.52 Cr is itself unreliable.
5. The neat-looking statements balance **only in the prior-year columns**; the FY26 column is a work-in-progress that has not been reconciled.

### To make it true, Anuj needs to:
- Bring in the **credit side** of Flexi/RTD (branch liabilities/equity or inter-unit payable) so the TB balances → fixes the ₹1.17 Cr.
- Correct the **SOCIE profit row** to ₹35.52 Cr and post **Reserves = ₹164.25 Cr** in both SOCIE and BS.
- Identify and eliminate the **₹54.57 Cr unsupported asset balance** (unbilled gross-up + branch assets + mapping gaps).
- Provide **current & deferred tax** and a **full-year depreciation** charge.
- Re-run the TB → it must show **Total DR = Total CR**, and BS **Total Assets = Total Equity & Liabilities** for FY26, before this can be called final.
