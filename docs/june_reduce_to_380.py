#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
june_reduce_to_380.py
=====================================================================
Applies the FY2025-26 "reduce Revised Gross to the 380-cr target" pass to the
JUNE salary workbook, at ROW LEVEL, using the documented skill mechanism:

    * Reduce  REVISED_ATTENDANCE_ALLOWANCE (GF, col 188)  -> lowers REVISED_GROSS (GG, 189)
    * OTHER_DEDUCTION (REVISED OTHER DEDUCTION, col 212)   absorbs the SAME amount
    * REVISED_TOTAL_DED (HI, col 217) is a *stored* value  -> reduce it by the same amount
    * REVISED_NET_PAYABLE (HJ, col 218) is SACROSANCT      -> never changed
      (invariant GG - HI = HJ is preserved because GG and HI both drop by the same d)

Constraints honoured (per the GROSS380 summary methodology):
    * OTHER DEDUCTION never goes negative
    * GF (attendance allowance) not pushed below 0
    * No ESI-EXEMPT employee taken below the Rs 21,000 gross ceiling
    * PF, ESI, BASIC, DA, NET PAYABLE all unchanged

Reduction is allocated COVERED-ROWS-FIRST (ESI-covered rows, then ESI-exempt rows).

Target: bring June's total REVISED_GROSS down to Rs 29,89,50,541 (the 380-cr summary
figure). The script computes the current total from the file and reduces the gap.

USAGE:
    python3 june_reduce_to_380.py "June_WITH_FORMULAE.xlsx"
Output: June_WITH_FORMULAE_FIXED.xlsx  (original is never overwritten)

After running, open the file in Excel / run your scripts/recalc.py so cached
formula values refresh; the GROSS380 summary then ties to Rs 380.00 cr.
=====================================================================
"""
import sys, shutil
from openpyxl import load_workbook

# ----------------------------- CONFIG --------------------------------
TARGET_JUNE_REVISED_GROSS = 298_950_541     # Rs 29,89,50,541  (380-cr summary figure)
ESI_EXEMPT_GROSS_FLOOR    = 21_000          # do not take an exempt employee below this
ROUND_DP                  = 2               # rupee decimals

# Header names to locate columns (case-insensitive, spaces/underscores ignored).
# Each entry: canonical_key -> list of acceptable header spellings, plus a
# fallback 1-based column index from the skill's column map.
COLMAP = {
    "GF_ATT_ALLOW":   (["REVISED ATTENDANCE ALLOWANCE", "REVISED_ATTENDANCE_ALLOWANCE"], 188),
    "GG_REV_GROSS":   (["REVISED GROSS", "REVISED_GROSS"],                                189),
    "OTHER_DED_212":  (["REVISED OTHER DEDUCTION", "OTHER DEDUCTION"],                    212),
    "HI_REV_TOTDED":  (["REVISED TOTAL DED", "REVISED_TOTAL_DED", "REVISED TOTAL DEDUCTION"], 217),
    "HJ_REV_NET":     (["REVISED NET PAYABLE", "REVISED_NET_PAYABLE", "NETPAYABLE"],      218),
    # used only to classify ESI-exempt rows (best-effort; safe fallback below):
    "ESI_DED":        (["ESIC", "ESI", "ESIC.1"],                                         None),
}
# ---------------------------------------------------------------------


def norm(s):
    return "".join(str(s).split()).replace("_", "").upper() if s is not None else ""


def find_header_row(ws, want_norms, scan=15):
    """Return (header_row_index, {colkey: col_idx})."""
    for r in range(1, scan + 1):
        vals = {norm(c.value): c.column for c in ws[r] if c.value is not None}
        hits = sum(1 for w in want_norms if w in vals)
        if hits >= 3:                      # enough key headers on this row
            return r, vals
    return None, {}


def resolve_columns(ws):
    want = []
    for spellings, _ in COLMAP.values():
        want += [norm(x) for x in spellings]
    hr, header = find_header_row(ws, want)
    resolved = {}
    for key, (spellings, fallback) in COLMAP.items():
        idx = None
        for sp in spellings:
            if norm(sp) in header:
                idx = header[norm(sp)]; break
        if idx is None and fallback is not None:
            idx = fallback                 # use skill's documented position
        resolved[key] = idx
    return hr, resolved


def num(v):
    if v is None: return 0.0
    if isinstance(v, str):
        if v.startswith("="): return None          # live formula
        v = v.replace(",", "").strip()
        if v in ("", "-"): return 0.0
        try: return float(v)
        except ValueError: return 0.0
    return float(v)


def main(path):
    out = path.rsplit(".", 1)[0] + "_FIXED.xlsx"
    shutil.copyfile(path, out)
    print(f"Loading {path} ...")
    wb = load_workbook(out)                         # data_only=False -> keep formulas
    # pick the sheet with the most rows (the salary data sheet)
    ws = max(wb.worksheets, key=lambda s: s.max_row)
    print(f"Data sheet: '{ws.title}'  ({ws.max_row} rows x {ws.max_column} cols)")

    hr, col = resolve_columns(ws)
    if hr is None:
        print("!! Could not auto-detect the header row. Edit COLMAP / check the sheet.")
    print(f"Header row: {hr}")
    for k, v in col.items():
        print(f"   {k:15s} -> column {v}")
    need = ["GF_ATT_ALLOW", "GG_REV_GROSS", "OTHER_DED_212", "HI_REV_TOTDED", "HJ_REV_NET"]
    if any(col[k] is None for k in need):
        sys.exit("!! Missing a required column; aborting. Set it manually in COLMAP.")

    data_start = (hr + 1) if hr else 2
    cGF, cGG, cOD, cHI, cHJ = (col["GF_ATT_ALLOW"], col["GG_REV_GROSS"],
                               col["OTHER_DED_212"], col["HI_REV_TOTDED"], col["HJ_REV_NET"])
    cESI = col.get("ESI_DED")

    rows = []
    gg_formula = od_formula = hi_formula = 0
    for r in range(data_start, ws.max_row + 1):
        gg = num(ws.cell(r, cGG).value)
        if gg is None: gg_formula += 1
        gf = num(ws.cell(r, cGF).value)
        od = num(ws.cell(r, cOD).value)
        hi = num(ws.cell(r, cHI).value);
        if ws.cell(r,cHI).value and str(ws.cell(r,cHI).value).startswith("="): hi_formula+=1
        hj = num(ws.cell(r, cHJ).value)
        esi = num(ws.cell(r, cESI).value) if cESI else 0.0
        if gg in (None, 0) and gf == 0 and od == 0:
            continue
        gg_v = gg if gg is not None else (num(ws.cell(r,col["GG_REV_GROSS"]).value) or 0)
        exempt = (esi == 0) and (gg_v or 0) > ESI_EXEMPT_GROSS_FLOOR
        rows.append(dict(r=r, gf=gf or 0, od=od or 0, hi=hi or 0, hj=hj or 0,
                         gg=gg_v or 0, exempt=exempt, gg_is_formula=(gg is None)))

    cur_total = sum(x["gg"] for x in rows)
    R = round(cur_total - TARGET_JUNE_REVISED_GROSS, ROUND_DP)
    print(f"\nCurrent REVISED_GROSS total : {cur_total:,.2f}")
    print(f"Target  REVISED_GROSS total : {TARGET_JUNE_REVISED_GROSS:,.2f}")
    print(f"Reduction to allocate (R)   : {R:,.2f}")
    if R <= 0:
        sys.exit("Nothing to reduce (already at/below target).")

    # capacity per row
    def cap(x):
        c = min(x["od"], x["gf"])                 # OD>=0 and GF>=0
        if x["exempt"]:
            c = min(c, x["gg"] - ESI_EXEMPT_GROSS_FLOOR)
        return max(c, 0.0)

    # covered-rows-first, then largest capacity for stable fill
    order = sorted(rows, key=lambda x: (x["exempt"], -cap(x)))
    remaining = R
    for x in order:
        if remaining <= 0: break
        d = round(min(remaining, cap(x)), ROUND_DP)
        if d <= 0: continue
        x["d"] = d
        remaining = round(remaining - d, ROUND_DP)
    if remaining > 1:
        print(f"\n!! WARNING: could not allocate Rs {remaining:,.2f} within constraints.")
        print("   (Total OTHER DEDUCTION / GF capacity is insufficient.) Review before use.")

    # apply
    applied = 0.0; touched = 0
    for x in rows:
        d = x.get("d", 0)
        if not d: continue
        ws.cell(x["r"], cGF).value = round(x["gf"] - d, ROUND_DP)
        ws.cell(x["r"], cOD).value = round(x["od"] - d, ROUND_DP)
        ws.cell(x["r"], cHI).value = round(x["hi"] - d, ROUND_DP)
        if not x["gg_is_formula"]:                 # GG stored value -> update it
            ws.cell(x["r"], cGG).value = round(x["gg"] - d, ROUND_DP)
        # HJ (net) deliberately untouched
        applied += d; touched += 1

    new_total = cur_total - applied
    print(f"\nRows touched                : {touched}")
    print(f"Reduction applied           : {applied:,.2f}")
    print(f"New REVISED_GROSS total     : {new_total:,.2f}  (Rs {new_total/1e7:.4f} cr)")
    print(f"Net Payable total           : {sum(x['hj'] for x in rows):,.2f}  (UNCHANGED)")
    if gg_formula: print(f"Note: REVISED_GROSS is a live formula on {gg_formula} rows (recalc to refresh).")
    print(f"\nSaved -> {out}")
    print("Next: open in Excel or run scripts/recalc.py so cached values refresh;")
    print("      the GROSS380 summary will then tie to Rs 380.00 cr.")
    wb.save(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 june_reduce_to_380.py <June_WITH_FORMULAE.xlsx>")
    main(sys.argv[1])
