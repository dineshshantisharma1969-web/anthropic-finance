# Pvt Ltd → LLP: Statutory Conversion vs. Liquidate-then-Form — Decision Note

A reference for the CA/board on the **two ways** to end up as an LLP, their tax
cost, and how partners subsequently take money out. Prepared as a planning note —
**not tax advice**; validate every figure against the company's actual position.

---

## 1. The two routes

| | **Route A — Statutory conversion** (LLP Act s.56 + Third Schedule; IT Act **Sec 47(xiiib)**) | **Route B — Liquidate + form fresh LLP** |
|---|---|---|
| Legal mechanism | Company converts into LLP by operation of law | Wind up the company (MVL/strike-off), then incorporate a new LLP |
| Capital gains on transfer | **Nil** if Sec 47(xiiib) conditions met | **Yes** — at shareholder level (Sec 46(2)) |
| Dividend tax | None | **Yes** — deemed dividend on reserves (Sec 2(22)(c)) |
| Stamp duty on assets | Usually exempt / concessional | **Full conveyance duty** on immovable property |
| Carry-forward losses & unabsorbed depreciation | Carry over (Sec 72A(6), conditions apply) | **Lapse** |
| MAT credit | Lapses | Lapses |
| Assets, PAN, contracts, licences | Transfer automatically | Fresh PAN/GST, re-execute contracts & licences |
| Typical timeline | Weeks | 9–15 months (MVL) |

**Bottom line:** Route A is materially cheaper and faster in almost every case.
Route B only makes sense when conversion is *blocked* — e.g. an unclearable
registered charge, shareholders who won't all become partners, or a
regulatory bar.

---

## 2. Route A — Statutory conversion (Sec 47(xiiib)) conditions

Conversion is **tax-neutral only if all** of these hold; breaching any one makes
the whole transfer taxable as capital gains:

1. All shareholders of the company become partners of the LLP — **and nobody else**.
2. Shareholders' capital + profit-sharing entitlement is in the **same proportion** as their shareholding at conversion.
3. **No consideration** other than a share in profit/capital of the LLP.
4. Erstwhile shareholders hold **≥ 50% of profit share for 5 years** post-conversion.
5. Company's **total sales/turnover/gross receipts ≤ ₹60 lakh** in each of the 3 preceding years, **and** total assets ≤ the prescribed limit *(verify current thresholds — these have been amended)*.
6. **No amount is paid** (directly or indirectly) to any partner out of the **accumulated profits** as on the date of conversion for **3 years**.

If turnover exceeds the s.47(xiiib) limit, conversion is still legally possible —
but it becomes a **taxable transfer** (loses the capital-gains exemption), which
narrows the gap with Route B.

---

## 3. Route B — Tax cost of liquidating the company

Winding up and distributing to shareholders triggers tax at **two (often three) levels**:

### (a) Deemed dividend — Sec 2(22)(c)
Distribution **to the extent of accumulated profits** (reserves & surplus, whether
capitalised or not, on the liquidation date) = **dividend** in shareholders' hands,
taxed at their **slab rate** (up to ~35.88%–39% with surcharge). TDS u/s 194 applies.

### (b) Capital gains — Sec 46(2)
On the balance received:

```
Capital gain = (money + FMV of assets received)
             − (portion already taxed as deemed dividend under 2(22)(c))
             − cost of acquisition of the shares
```

- Unlisted shares held **> 24 months = long-term** → **12.5% without indexation**
  (regime from 23 July 2024; the old 20%-with-indexation no longer applies).
- Held ≤ 24 months = short-term → slab rate.

### (c) Company-level tax — Sec 46(1)
The company is **not** taxed merely for distributing assets *in specie*. **But** if
it **sells assets to raise cash** before distributing, those sales are taxed at the
company as capital gains / business income (**corporate rate 22–25%+**) *first*.

### (d) Other one-time costs
- **Stamp duty** on immovable property moving to the new LLP (full conveyance, ~5–7% state-wise).
- **GST**: slump sale of business as a going concern is exempt; itemised asset sale is taxable.
- **Loss of** carry-forward losses, unabsorbed depreciation and MAT credit.
- Liquidator / NCLT / professional fees for MVL.

### Illustrative one-time hit (defaults in the calculator)
Reserves ₹50 L, distribution ₹70 L, share cost ₹10 L, no asset-realisation gain,
no immovable property, shareholders at 31.2%:

| Head | Amount |
|---|---|
| Deemed dividend tax (₹50 L × 31.2%) | ₹15,60,000 |
| LTCG Sec 46(2) — (₹70 L − ₹50 L − ₹10 L) × 12.5% | ₹1,25,000 |
| Corporate tax on asset realisation | ₹0 |
| Stamp duty | ₹0 |
| **Total one-time cost of Route B** | **₹16,85,000** |

The statutory conversion avoids essentially all of this (nominal filing/professional cost only).

### Closure mechanism for Route B
- **Members' Voluntary Liquidation (MVL), IBC 2016** — solvent company **with assets**: appoint liquidator, realise/distribute, NCLT dissolution.
- **Strike-off, Sec 248 (Form STK-2)** — only if **dormant with negligible assets/liabilities**; distribute/clear assets first (triggering the taxes above), then strike off.

---

## 4. Withdrawing money from the LLP bank account (both routes)

Once the LLP is running, trace **where the cash came from**:

**Capital you introduced** (e.g. post-tax liquidation proceeds put into the LLP):
your own money — introduction is not taxed, and withdrawing it back is
**repayment of capital / drawings, not income** (keep the capital account positive).

**Profits the LLP earns** — four routes:

| Route | Taxable to partner? | Deductible for LLP? |
|---|---|---|
| **Share of profit** (50:50) | No — exempt u/s **10(2A)** | already taxed in LLP |
| **Remuneration** (working partners) | Yes — slab | Yes, within **Sec 40(b)** cap |
| **Interest on capital** | Yes — slab | Yes, up to **12% p.a.** |
| **Capital drawings** | No — own money | n/a |

The interactive calculator (`index.html`) models the optimal split, the per-partner
take-home, and a **month-by-month cash-flow** of these drawings against the LLP bank
balance.

---

## 5. Recommendation

Default to **Route A (statutory conversion)** unless a specific, documented barrier
forces Route B. Quantify both on the company's **actual reserves, share cost, asset
values and shareholder slabs** before deciding — the calculator's *Route comparison*
card does exactly this. Then have the CA confirm the current-year Sec 47(xiiib)
thresholds and LTCG/stamp-duty rates.
