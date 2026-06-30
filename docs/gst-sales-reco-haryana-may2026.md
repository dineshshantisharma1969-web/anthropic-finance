# GST Sales Reconciliation — Haryana, May 2026

**Entity:** Impressions Services Private Limited
**Registration / State:** Haryana (state code 06)
**Return:** GSTR-1 — Tax period May 2026 (document series `06/26-27`)
**Source file:** `GST RECO 2025-26 / GSTR-1_Haryana_May-26.xlsx` (Google Drive)
**Reconciliation date:** 30 June 2026

> Scope of this reco: the GSTR-1 workbook contains both the **books sales register**
> (sheet `Invoice Wise Details`, voucher-wise from the accounting system) and the
> **GSTR-1 return data** (sheets `b2b`, `b2cs`, `cdnr`, `exemp`, `hsn`, `docs`) together
> with the **e-invoice auto-population** (sheets `E-invoice`, `E-cdnr`). The reco therefore
> covers three layers: **Books ↔ GSTR-1 ↔ E-invoice (IRN)**, plus the internal
> HSN and document-summary cross-checks.

---

## 1. Result at a glance

| Reconciliation | Result |
|---|---|
| Books sales register ↔ GSTR-1 (all sections) | ✅ **Matches to the rupee** |
| Invoice-level Books B2B ↔ GSTR-1 B2B (642 invoices) | ✅ 0 missing, 0 value differences |
| HSN summary ↔ net outward supplies (value & tax) | ✅ **Ties exactly** |
| E-invoicing coverage of B2B | ⚠️ 1 invoice short-covered (see §5) |
| Cancelled documents vs deleted e-invoices | ✅ Consistent (5 + 2) |

**One actionable item:** invoice `SP/06/26-27/0012` is reported in books and GSTR-1 at
₹29,765 taxable but the live e-invoice (IRN) covers only ₹16,920 — a shortfall of
**₹12,845 taxable / ₹2,312.10 tax** with no active IRN.

---

## 2. Net outward tax liability per GSTR-1 (after credit notes)

| Particulars | Taxable Value | IGST | CGST | SGST |
|---|---:|---:|---:|---:|
| B2B (4A/4B/4C/6B/6C) | 1,04,175,980.32 | 3,711,969.88 | 7,132,280.63 | 7,132,280.63 |
| B2C Small (7) | 157,467.13 | 0.00 | 14,066.74 | 14,066.74 |
| Exempt / Nil / Non-GST (8) | 4,980,150.62 | 0.00 | 0.00 | 0.00 |
| **Less:** Credit Notes – Registered (9B) | (1,312,265.20) | (49,165.87) | (93,095.93) | (93,095.93) |
| **Net outward supplies** | **10,80,01,332.87** | **3,662,804.01** | **7,053,251.44** | **7,053,251.44** |

**Total tax liability (IGST+CGST+SGST): ₹1,77,69,306.89**

> B2CL (5), Exports (6), Advances (11A/11B) and CDNUR (9B) are **NIL** for the period.

---

## 3. Books ↔ GSTR-1 (section-level tie-out)

The `Invoice Wise Details` register is structured in the same four blocks as the return.
Each block total equals the corresponding GSTR-1 section exactly:

| Section | Books Taxable | GSTR-1 Taxable | Diff | Books Tax (C+S+I) | GSTR-1 Tax | Diff |
|---|---:|---:|:--:|---:|---:|:--:|
| B2B | 1,04,175,980.32 | 1,04,175,980.32 | 0 | 17,976,531.14 | 17,976,531.14 | 0 |
| B2CS | 157,467.13 | 157,467.13 | 0 | 28,133.48 | 28,133.48 | 0 |
| CDNR | 1,312,265.20 | 1,312,265.20 | 0 | 235,357.73 | 235,357.73 | 0 |
| Exempt | 4,980,150.62 | 4,980,150.62 | 0 | 0 | 0 | 0 |

**Invoice-level:** 642 B2B invoices in books, 642 in GSTR-1 B2B — **no invoice missing
on either side, and no taxable-value difference on any matched invoice.**

---

## 4. HSN summary ↔ outward supplies cross-check

The HSN-wise summary (`hsn(b2b)` + `hsn(b2c)`) must equal the net of all supply sections:

| | Taxable Value | IGST | CGST | SGST |
|---|---:|---:|---:|---:|
| HSN summary total | 1,08,001,332.87 | 3,662,804.01 | 7,053,251.44 | 7,053,251.44 |
| Net outward supplies (§2) | 1,08,001,332.87 | 3,662,804.01 | 7,053,251.44 | 7,053,251.44 |
| **Difference** | **0.00** | **0.00** | **0.00** | **0.00** |

✅ HSN summary ties to the return value-for-value and tax-for-tax.

---

## 5. E-invoicing (IRN) coverage of B2B

All 642 B2B invoices carry a valid IRN. The gross e-invoice total exceeds the filed B2B
total; the difference is fully explained:

```
E-invoice taxable total            1,05,663,075.65
Less: B2B taxable (filed)          1,04,175,980.32
Difference                              1,487,095.33
  = Deleted/cancelled e-invoices (5)   1,499,940.33
  − SP/06/26-27/0012 e-invoice short      (12,845.00)
```

### 5.1 Cancelled invoices ↔ deleted e-invoices (consistent ✅)
Five `SA` invoices were e-invoiced and later **Deleted** (status = "Deleted"); they are
correctly **excluded** from the filed B2B table. These match the 5 cancelled `SA`
invoices in the document summary (§6).

| Cancelled e-invoice (Deleted) | Recipient | Taxable |
|---|---|---:|
| SA/06/26-27/0445 | JLL Property Consultants | 102,498.00 |
| SA/06/26-27/0494 | JLL Property Consultants | 540,929.26 |
| SA/06/26-27/0811 | JLL Building Operations | 820,578.44 |
| SA/06/26-27/0982 | JLL Property Consultants | 35,933.63 |
| SA/06/26-27/0954 | 3E Education Trust | 1.00 |

*Action: confirm each was genuinely cancelled / re-issued under a fresh number.*

### 5.2 ⚠️ Short-covered e-invoice — ACTION REQUIRED
| Invoice | Books taxable | GSTR-1 B2B taxable | Active e-invoice taxable | Gap |
|---|---:|---:|---:|---:|
| **SP/06/26-27/0012** (JLL Property Consultants) | 29,765.00 | 29,765.00 | 16,920.00 | **12,845.00** |

Books and GSTR-1 agree, but the live IRN covers only ₹16,920. **₹12,845 taxable
(₹2,312.10 tax) is reported without an active e-invoice.**
*Action: generate an IRN for the balance or reconcile the e-invoice value.*

---

## 6. Document summary reconciliation

| Nature of document | Series | Issued | Cancelled | Net |
|---|---|---:|---:|---:|
| Tax invoices | SA/06/26-27/0442–1018 | 577 | 5 | 572 |
| Tax invoices | SP/06/26-27/0011–0021 | 11 | 0 | 11 |
| Tax invoices | ST/06/26-27/0094–0191 | 98 | 1 | 97 |
| Credit notes | CN/06/26-27/0026–0057 | 32 | 2 | 30 |

Net tax invoices issued **680**; net credit notes **30**. The 5 cancelled `SA` invoices
correspond to the 5 deleted e-invoices in §5.1, and the 30 net credit notes agree with
the CDNR block (28 registered + 2 cancelled in numbering).

---

## 7. Conclusion

The GSTR-1 for Haryana, May 2026 is **internally consistent and fully reconciled with
the books of account.** Books = GSTR-1 = HSN, to the rupee. The only open item is the
e-invoice shortfall on **`SP/06/26-27/0012` (₹12,845 taxable)**, which should be
regularised. The five deleted e-invoices should be confirmed as legitimately cancelled.
