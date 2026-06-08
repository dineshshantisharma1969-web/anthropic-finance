# Purchase Order Generation — Udhas Nath Baba Services (UNBS)

Scripts that fill the blank Impressions PO template (`PO_Blank_*.docx`) for the
vendor **Udhas Nath Baba Services Pvt Ltd**, using:

- **Supplier / GST / address** and **buyer (Impressions Delhi) details** taken from the sample tax-invoice PDFs.
- **Amounts** taken only from the columnar Excel ledger (`UNBS DETAILS.xlsx`),
  from the `CONTRACTOR CHARGE-18%` and `HIRE CHARGES` columns.
- **Description** derived from the ledger column:
  - Contractor Charge rows -> *"Supervisory Cleaning Services Charges ..."* (HSN 998311)
  - Hire Charge rows -> *"Machine Cleaning Hire Charges ..."* (HSN 997319)
- **PO date** = 4 days before the ledger entry date.

## Files
- `gen_pos.py` — reads `blank.docx` (the PO template) and writes one filled
  `.docx` per ledger entry into `po_out/`. Includes an Indian-format number /
  amount-in-words helper. The 12 PO records are defined inline in `recs`.
- `combine.py` — merges the generated POs into a single `UNBS_POs_ALL_12.docx`
  with one PO per page.

## Usage
```bash
pip install python-docx
# place the blank PO template next to the scripts as blank.docx
python3 gen_pos.py
python3 combine.py
```

## Conventions used
- PO numbers: `IMP/PO/UNBS/2324/01..12` (sequential, adjust as needed).
- Payment Terms: "AS MUTUALLY AGREED".
- Line: Qty 1, Unit "Nos", Rate = full taxable amount; IGST 18%.
- "Amount" column = taxable value; Grand Total = taxable + 18% IGST
  (reconciles to the ledger gross amount).
