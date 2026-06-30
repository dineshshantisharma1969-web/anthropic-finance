---
name: gst-sales-reco
description: >-
  Perform a GST outward-supply (sales) reconciliation from a GSTR-1 export workbook
  on Google Drive. Use when the user asks to "do a GST sales reco", reconcile GSTR-1
  / outward supplies / sales register, check e-invoice coverage, or validate a GSTR-1
  before filing. Reconciles Books (sales register) ↔ GSTR-1 sections ↔ E-invoice (IRN),
  plus the HSN and document-summary cross-checks, and flags actionable discrepancies.
---

# GST Sales Reconciliation

Reconcile a period's outward supplies across three layers and produce a report:

```
Books sales register  ↔  GSTR-1 return sections  ↔  E-invoice (IRN) data
                          + HSN summary cross-check
                          + document-summary cross-check
```

The source is a GSTR-1 export `.xlsx` (one workbook per GSTIN/state per month), kept in
Drive folders named like **`GST RECO 2025-26`**. Each workbook bundles the books register,
the GSTR-1 sections, the HSN/document summaries, and the e-invoice auto-population — so the
whole reco runs off a single file.

## When to use
- "Carry out / do a GST sales reco for <state> <month>"
- "Reconcile GSTR-1 with books / sales register"
- "Check e-invoice (IRN) coverage of my B2B"
- "Validate this GSTR-1 before filing"

## Inputs to confirm first
1. **Which file/period/state.** Search Drive for the `GST RECO ...` folder and list its
   workbooks. If several states/months exist, ask which one (or do all).
2. Output location: a markdown report in `docs/` (default) and/or a summary uploaded to
   the same Drive folder.

## Procedure

### Step 1 — Locate and download the workbook
Use the Google Drive tools (`search_files`, then `download_file_content` with the file id)
to fetch the `.xlsx` as base64; decode to a local file. `read_file_content` flattens all
sheets into one blob and is unreliable for totals — **always parse the real `.xlsx`** with
`openpyxl` (`pip install openpyxl` if missing), `data_only=True`.

### Step 2 — Understand the sheets
A standard GSTR-1 export has these tabs (some may be NIL/empty):

| Sheet | Meaning |
|---|---|
| `Invoice Wise Details` | **Books** sales register, voucher-wise. Stacked sub-blocks (B2B, B2CS, CDNR, EXEMP), each with its own header row and a `TOTAL` row. |
| `b2b`, `b2cs`, `b2cl` | GSTR-1 B2B / B2C-small / B2C-large tables |
| `cdnr`, `cdnur` | Credit/debit notes (registered / unregistered) |
| `exp`, `at`, `atadj`, `exemp` | Exports, advances received/adjusted, exempt-nil-nonGST |
| `hsn(b2b)`, `hsn(b2c)` | HSN-wise summaries |
| `docs` | Summary of documents issued (series, count, cancelled) |
| `E-invoice`, `E-cdnr` | IRN auto-populated invoices/credit notes (note the `E-invoice status` column: `Valid` / `Deleted`) |

Parsing notes:
- Numbers may be strings with commas / `-` for zero — coerce safely (`-`, `''`, `–` → 0).
- In `Invoice Wise Details`, **split by sub-block** (each starts with the entity name +
  section title + a `VoucherNo` header and ends with a `TOTAL` row). Don't parse it as one
  flat table or repeated headers/credit-note rows will corrupt the totals.
- Match invoices by **invoice/document number** (trimmed string).

### Step 3 — Run the four reconciliations

1. **Books ↔ GSTR-1, section totals.** For B2B, B2CS, CDNR, EXEMP compare taxable value
   and tax (CGST/SGST/IGST). Expect 0 difference.
2. **Books B2B ↔ GSTR-1 B2B, invoice-level.** Report invoices only in books, only in
   GSTR-1, and matched invoices with a taxable-value difference > ₹1.
3. **HSN ↔ net outward supplies.** `hsn(b2b)+hsn(b2c)` totals must equal
   `B2B + B2CS + B2CL + Exports + Exempt − CDNR` for taxable **and** each tax head.
4. **E-invoice coverage.** Every taxable B2B invoice should have a `Valid` IRN.
   - B2B invoices with no IRN → under-coverage (flag).
   - IRN docs not in B2B → usually `Deleted`/cancelled e-invoices (reconcile to the
     cancelled count in `docs`); if `Valid` and missing from B2B, that is an omission.
   - Matched invoices where B2B taxable > active-IRN taxable → **short-covered e-invoice**
     (the gap has no live IRN — flag as action required).
   - Prove the tie-out: `E-invoice total − B2B total = Σ(deleted IRNs) − Σ(B2B-over-IRN gaps)`.

### Step 4 — Document-summary cross-check
From `docs`, compute net documents = issued − cancelled per series, and check cancelled
invoices correspond to `Deleted` e-invoices and that credit-note counts agree with CDNR.

### Step 5 — Write the report
Produce `docs/gst-sales-reco-<state>-<month><year>.md` with: result-at-a-glance table,
net tax liability, the four tie-outs, an explicit e-invoice tie-out block, and a clearly
labelled **action-required** list. Lead with whether it reconciles to the rupee and the
single most important open item. Optionally upload a copy to the Drive folder.

## Reference implementation
A worked, rupee-tied example is in `docs/gst-sales-reco-haryana-may2026.md`
(Impressions Services Pvt Ltd, Haryana, May 2026). The parsing/reconciliation logic above
was validated against it: Books = GSTR-1 = HSN exactly, with one short-covered e-invoice
surfaced as the only action item.

## Output principles
- Report rupee amounts with thousands separators; keep paise.
- Every claimed match must be a computed difference, not an assumption — show the number.
- Distinguish **explained** differences (cancelled IRNs) from **action-required** ones.
- Never silently drop rows; if a sub-block or sheet is skipped, say so.
