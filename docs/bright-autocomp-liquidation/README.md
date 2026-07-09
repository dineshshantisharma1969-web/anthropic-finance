# Bright Autocomp Pvt Ltd — Liquidation Tax Model

Works out the tax of **liquidating Bright Autocomp Private Limited** and distributing
to its two shareholders (Bikram Singh Chadha 50% · Sonu Chadha 50%), at **both** the
company and shareholder level. Built from the audited FY2024-25 financials.

> Figures in the financials are in **Rs. '00**; everything here is in **actual Rupees**.
> **Planning model, not tax advice** — validate with your CA.

## Files

| File | What it is |
|---|---|
| `Bright_Autocomp_Liquidation_Tax.xlsx` | **Editable workbook, live formulas.** Three sheets — see below. |
| `Bright_Autocomp_Liquidation_Tax.docx` | Word summary of the tax implications. |
| `build_liquidation_model.py` | Reproducible builder — regenerates both files. |

## The workbook (3 sheets)

1. **Liquidation Tax Model** — the full computation. Yellow cells are editable
   (land market value, LTCG rate, surcharge, cess, shareholder slab, share cost).
   Enter the **Manesar land market value** and everything recalculates.
2. **Land FMV Scenarios** — a **side-by-side table**: type several land market
   values across the top row and read the company CG tax, deemed dividend,
   shareholder tax, total tax and net-in-hand for each.
3. **Shareholder Tax** — splits everything a shareholder receives into three
   buckets — ① return of capital (tax-free), ② deemed dividend (slab),
   ③ capital gains u/s 46(2) — with the tax on each.

## Key figures (from the financials)

| Item | Amount (₹) |
|---|---|
| Paid-up share capital (10,000 × ₹10) | 1,00,000 |
| Reserve & Surplus (accumulated profits) | 51,89,668 |
| Land & Building — book value (Manesar plot, 0% dep.) | 1,45,74,847 |
| Total external liabilities (incl. ₹1.54 cr related-party loan) | 1,57,63,264 |
| Net assets at book | 52,89,668 |

## How the tax works

- **Company level (Sec 45/46(1)):** if assets are **sold** to raise cash — chiefly
  the Manesar land — the company pays **12.5% LTCG + surcharge + cess** on the gain
  over cost, *before* distributing.
- **Shareholder level (Sec 2(22)(c)):** the distribution, to the extent of
  **accumulated profits**, is a **deemed dividend** taxed at each shareholder's slab.
- **Shareholder level (Sec 46(2)):** anything above (deemed dividend + cost of
  shares) is **capital gains**. The **return of paid-up capital is tax-free** —
  it equals the cost of shares.

## Illustrative results (default rates: 12.5% LTCG, 12% surcharge, 31.2% slab)

| Land market value | Company CG tax | Deemed dividend | Total tax | Net to shareholders |
|---|---|---|---|---|
| ₹1.46 cr (book) | ₹0 | ₹51.9 L | **₹16.2 L** | ₹36.7 L |
| ₹2.5 cr | ₹15 L | ₹1.41 cr | **₹59 L** | ₹98 L |
| ₹5 cr | ₹52 L | ₹3.55 cr | **₹1.62 cr** | ₹2.45 cr |
| ₹10 cr | ₹1.24 cr | ₹7.82 cr | **₹3.68 cr** | ₹5.39 cr |
| ₹15 cr | ₹1.97 cr | ₹12.09 cr | **₹5.74 cr** | ₹8.33 cr |

Effective tax rises from ~30.6% (book) to ~40.8% as the land value grows — the
**land FMV is the driver**.

## Important

- The **₹1.54 cr related-party loan** and all creditors must be repaid before
  shareholders receive anything.
- **TDS u/s 194** may apply on the deemed dividend.
- Forming an LLP **after** liquidation does **not** reduce the company's capital-gains
  tax — that is triggered by the asset sale itself. Only a **statutory conversion**
  under **Sec 47(xiiib)** (instead of liquidating) avoids the company-level tax
  entirely. See `../llp-partner-withdrawal-calculator/`.
