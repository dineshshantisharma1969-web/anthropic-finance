# SKILL — GSTR-1 Books vs Portal Reconciliation (Rules G1–G4)

> Part of the GST second brain (`docs/gst-knowledgebase/`). Run this **before
> filing every GSTR-1** (books vs the portal's auto-drafted R1 / e-invoice data)
> and again **after filing** (books vs filed R1) for the permanent record.
> Same discipline as the salary reconciliation skill: deterministic script,
> exception buckets, working columns, nothing cleared without a reason.

## Purpose

Books (sales register) and the GST portal must agree, invoice by invoice, on:

1. **Bill/Invoice number**
2. **Taxable value (amount)**
3. **GST rate**
4. **GST amount** (IGST + CGST + SGST)

Any gap is either revenue reported but not taxed (portal short → interest +
notice risk under S.73/74) or tax paid on unbooked revenue (portal excess →
working-capital leak, amendment needed). This reco finds both.

## Inputs

| Side | File | Where from |
|---|---|---|
| **BOOKS** | Sales register (xlsx/csv) — one row per invoice or per invoice-rate line | Accounting system (Tally/ERP export) |
| **PORTAL** | GSTR-1 Excel/CSV — `b2b` sheet | GST portal → Returns → GSTR-1 → *Download details* (auto-drafted before filing, or filed R1 after) |

The script auto-detects columns by header name (invoice no / bill no, GSTIN,
taxable value, rate, IGST/CGST/SGST or total tax) and auto-finds the header row
(portal exports have summary rows on top). Credit notes (`cdnr` sheet): run a
second pass with the CDN sheet on both sides, or net them in books first.

## How to generate

```
python gstr1_reco.py <books.xlsx|csv> <portal.xlsx|csv> <out_RECO.xlsx> [--tol 1]
                     [--books-sheet NAME] [--portal-sheet NAME]
```

(script beside this file; needs `pip install openpyxl`)

## Rules

### G1 — Match key: normalized invoice number (+ GSTIN when both sides have it)

Invoice numbers differ cosmetically between ERP and portal (`INV-0045` vs
`INV0045` vs `inv/45`). Normalize before matching:
uppercase → drop all non-alphanumerics → **pass 2**: also strip leading zeros
inside numeric runs (`INV0045` ≡ `INV45`). If both sides carry recipient GSTIN,
the key is `GSTIN + invoice no` (two customers can share a bill number);
otherwise invoice no alone. Rows are **aggregated to invoice level** first
(books often has one row per rate line; portal b2b has one row per invoice+rate).

### G2 — Compare with a rounding tolerance, never blindly

Per matched invoice compare: taxable value, total GST amount, and the **set of
rates**. Default tolerance **₹1 per invoice** (rounding); configurable via
`--tol`. If a side has no tax columns, GST amount = Σ(taxable × rate / 100).
A tolerance only forgives rounding — it never forgives a rate difference:
same value at 12% vs 18% is always an exception.

### G3 — Exception buckets and their standard actions

| Bucket | Meaning | Standard action |
|---|---|---|
| `MATCHED` | All four fields agree within tolerance | None — audit trail |
| `MISMATCH — TAXABLE_DIFF` | Same invoice, different taxable value | Fix whichever side is wrong; portal fix = amend in next R1 (Table 9A) |
| `MISMATCH — RATE_DIFF` | Same invoice, different rate(s) | Classification call — check the rate NN for the service/goods; record outcome in `positions/POSITIONS.md` |
| `MISMATCH — TAX_DIFF` | Values/rates agree but tax differs | Usually POS / IGST-vs-CGST+SGST split error — check place of supply |
| `BOOKS_ONLY` | In books, not on portal | **Tax short-paid.** Add in current R1 before filing (or amend next period). Interest runs @18% u/s 50 — the clock is why this reco runs monthly |
| `PORTAL_ONLY` | On portal, not in books | Duplicate upload / cancelled invoice not deleted / booking missed. Verify books; if portal wrong, amend (Table 9A) or issue CDN |

### G4 — Amendment tracking discipline

Every exception carries working columns `ACTION` / `AMEND_IN_PERIOD` / `REMARKS`
in the output. When an amendment is filed, record the period it went into —
an exception is closed only when a later month's reco shows the two sides equal.
Log recurring root causes (e.g. ERP rounding, a branch uploading late) in
`positions/POSITIONS.md` so they get fixed at source, not re-reconciled forever.

## Output: `<Period>_GSTR1_RECO.xlsx` — five tabs

| Tab | Contents |
|---|---|
| **SUMMARY** | Counts + taxable + tax by bucket; net tax at stake (books vs portal) |
| **MISMATCH** | Matched invoices failing G2 — side-by-side books/portal values, per-field diff, reason flags; biggest tax gap first |
| **BOOKS_ONLY** | Missing from portal — sorted by tax, working columns |
| **PORTAL_ONLY** | Extra on portal — sorted by tax, working columns |
| **MATCHED** | Full matched list (audit trail) |

Working order: `BOOKS_ONLY` first (interest clock running), then `MISMATCH` by
tax-gap size, then `PORTAL_ONLY`.
