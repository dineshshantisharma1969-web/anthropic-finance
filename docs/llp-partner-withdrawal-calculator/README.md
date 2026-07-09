# LLP Partner Withdrawal &amp; Tax Calculator

An interactive, self-contained calculator for a **Pvt Ltd &rarr; LLP** conversion,
set up for **two partners on an equal (50:50) profit-sharing ratio**. It models how
each partner draws money out of an LLP (remuneration + interest on capital + profit
share), applies the tax at the firm and each partner's level, and compares the total
tax against staying a Pvt Ltd (salary + dividend).

## What it answers

> After converting, how should partners split their drawings, and how much tax do
> we actually save versus the company route?

## Files

| File | What it is |
|---|---|
| `index.html` | **The calculator** — open in any browser, no network needed. Firm + per-partner inputs, LLP firm split, Section 40(b) cap, per-partner take-home, a **12-month cash-flow** of drawings vs the bank balance, a **conversion-vs-liquidation** one-time-cost comparison, and an LLP-vs-Pvt-Ltd side-by-side. |
| `liquidation-vs-conversion.md` | **Decision note** — statutory conversion (Sec 47(xiiib)) vs liquidate-then-form-LLP: conditions, the deemed-dividend / Sec 46(2) capital-gains / stamp-duty tax hit of liquidating, and how partners withdraw afterwards. Reference for your CA. |
| `README.md` | This file. |

## The four ways a partner takes money out of an LLP

| Route | Taxable to partner? | Deductible for LLP? |
|---|---|---|
| **Share of profit** | No — exempt u/s **10(2A)** | (already taxed in the LLP) |
| **Remuneration / salary** (working partners) | Yes — slab | Yes — within **Sec 40(b)** cap |
| **Interest on capital** | Yes — slab | Yes — up to **12% p.a.** |
| **Drawings / capital withdrawal** | No — it's your own capital | n/a |

## Why an LLP usually beats a Pvt Ltd for owner payouts

- A company pays corporate tax, **then** dividends are taxed *again* in the
  shareholder's hands — double taxation.
- In an LLP the profit share is **tax-free** once distributed (taxed only once, at
  the LLP), and remuneration + interest are **deductible**, shrinking the taxable base.
- No dividend distribution tax / DDH.

## How the model works

**LLP side**
1. `Interest on capital = capital × min(rate, 12%)` — deductible.
2. `Book profit (for 40(b)) = profit − interest`.
3. `Max deductible remuneration` per Section 40(b) (FY 2024-25 onwards): higher of
   &#8377;3,00,000 or 90% on the first &#8377;6,00,000 of book profit, then 60% on the balance.
4. `LLP taxable income = book profit − allowed remuneration` (any remuneration above
   the cap is disallowed and stays taxable).
5. `LLP tax = 30% + 12% surcharge (if income > ₹1 cr) + 4% cess`.
6. `Profit share = profit − interest − remuneration − LLP tax` → **tax-free** to partners.
7. Remuneration + interest are taxed at the partners' marginal slab.

**Pvt Ltd side (comparison)** — same salary drawn; residual profit taxed at the
corporate rate (default Sec 115BAA, 25.168%), distributed as dividend, taxed again at
the shareholder's marginal rate.

**Monthly cash-flow** — spreads the annual drawings across Apr→Mar: remuneration monthly,
interest & profit share either monthly or as a March lump, LLP tax via advance-tax
instalments (15/45/75/100%) or evenly. Flags any month the bank balance goes negative.
A **Download CSV** button exports the month-by-month table (raw numbers, Excel-ready) for
your CA.

**Capital withdrawal** — how much contributed capital partners can pull out **tax-free**
(return of capital is not income). Gated by three tests the panel checks: the LLP
agreement must permit it, the LLP must stay solvent (capital − liabilities), and — if the
capital came from a converted company's **reserves** — the Sec 47(xiiib) **36-month lock**
(withdrawing within 3 years breaches tax-neutrality and makes the whole conversion taxable).

**Conversion vs liquidation** — the one-time cost of *winding up the company first*:
deemed dividend on reserves (Sec 2(22)(c)), capital gains on shares (Sec 46(2) @ 12.5%),
corporate tax on asset realisation, and stamp duty — versus ~₹0 for the statutory
conversion. See `liquidation-vs-conversion.md` for the full write-up.

**Worked example** — two equal partners (₹1 cr book profit, ₹25 L capital each @ 12%,
optimise mode, both at 31.2%, 115BAA company):

| | LLP | Pvt Ltd |
|---|---|---|
| Total tax (entity + both owners) | **₹31.20 L** | ₹37.40 L |
| In owners' hands (combined) | **₹68.80 L** | ₹62.60 L |
| Each partner takes home | **₹34.40 L** | ₹31.30 L |

→ LLP saves **₹6.20 L** of tax and puts **₹6.20 L** more in the partners' hands on the
same profit — about **₹3.10 L extra per partner**.

## Assumptions &amp; caveats

- **Planning tool, not tax advice** — confirm every figure with your CA.
- Two partners, **equal 50:50** profit-sharing ratio; both treated as working partners.
  Total remuneration is capped at the firm-level Section 40(b) limit and split 50:50.
- Section 40(b) limits, the 115BAA rate, surcharge slabs and cess are as understood for
  **FY 2025-26 (AY 2026-27)**; these change — re-verify current-year numbers.
- Remuneration &amp; interest are deductible **only if authorised and quantified in the LLP
  agreement**.
- The comparison ignores MAT/AMT, TDS timing, and state-specific items.
- **Tax-neutral conversion under Sec 47(xiiib)** (turnover/asset thresholds, 50%
  profit-share continuity for 5 years, no payout from accumulated profits for 3 years)
  is a separate test — breaching it triggers capital-gains tax on the conversion itself.
  Not modelled here.
