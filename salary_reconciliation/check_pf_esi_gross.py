#!/usr/bin/env python3
"""
Salary reconciliation sanity checks — PF 12%, ESI 0.75%/ceiling, and full-month
gross projection — run month-by-month over the RECONCILED monthly salary files.

Implements the three checks requested, exactly per PF_SALARY_RECONCILIATION_SKILL_v4.md
and the build_*_management_review.py reference pipeline:

  CHECK 1  PF = 12% of (REVISED_BASIC + REVISED_DA)        [skill check C3]
           For every row with REVISED_PF > 0, REVISED_PF must equal
           0.12 * (REVISED_BASIC + REVISED_DA) within +/- Re 1.

  CHECK 2  PF present in ECR  =>  Basic + DA should normally be < 15,000
           PF wage ceiling is Rs 15,000 (=> employee PF <= Rs 1,800).
           For rows where the ECR PF column is populated (ECR_PF > 0), the
           revised Basic + DA should normally sit at/under the 15,000 ceiling.
           Rows above it are the *exceptions* (genuine high earners who
           contribute PF above the ceiling) — listed, not treated as errors.
           Also reports the full-month Basic+DA projection > 15,000 view (M6).

  CHECK 3  ESI mirror of the PF logic
           (a) For rows with REVISED_ESIC > 0, REVISED_ESIC must equal
               0.0075 * REVISED_GROSS within +/- Re 1.
           (b) ESI present  =>  REVISED_GROSS should normally be <= 21,000
               (ESI wage ceiling). Rows above it are the exceptions.

  CHECK 4  Employees whose gross, if worked for the whole month, is way too high
           full-month gross = REVISED_GROSS * FULL_MONTH / ADJ_WORKING_DAYS
           (the MONTHLY_GROSS_PROJECTION column). Rows are bucketed and the
           top offenders are listed so absurd projections stand out.

USAGE
    python check_pf_esi_gross.py <folder_with_monthly_xlsx> [--out report.xlsx]

    <folder> should contain files named by month, e.g. April.xlsx ... March.xlsx
    (the RECONCILED folder). Each file is read from its first sheet.

Outputs a per-month console summary and, with --out, a multi-sheet Excel report
(one Summary sheet plus per-month exception sheets).
"""

import argparse
import calendar
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---- tolerances / statutory constants -------------------------------------
RUPEE_TOL   = 1.0       # money checks pass within +/- Re 1
PF_CEILING  = 15000     # PF wage ceiling (Basic + DA)
PF_MAX_EE   = 1800      # 12% of 15,000
ESI_CEILING = 21000     # ESI wage ceiling (gross)
PF_RATE     = 0.12
ESI_RATE    = 0.0075

# "way too high" gross-projection buckets (full-month equivalent gross)
GROSS_PROJ_HIGH    = 50000     # notable
GROSS_PROJ_ABSURD  = 100000    # implausible for this workforce

# Month -> calendar days. Financial year Apr..Mar, year inferred (FY 2025-26).
FY = {
    "april": (2025, 4), "may": (2025, 5), "june": (2025, 6), "july": (2025, 7),
    "august": (2025, 8), "september": (2025, 9), "october": (2025, 10),
    "november": (2025, 11), "december": (2025, 12), "january": (2026, 1),
    "february": (2026, 2), "march": (2026, 3),
}
MONTH_ORDER = ["April", "May", "June", "July", "August", "September",
               "October", "November", "December", "January", "February", "March"]


def full_month_days(stem: str) -> int:
    """Calendar days for a file named like 'December' / 'December.xlsx'."""
    key = stem.strip().lower()
    if key in FY:
        y, m = FY[key]
        return calendar.monthrange(y, m)[1]
    return 31  # safe default


def norm(name: str) -> str:
    """Normalise a column name for tolerant matching."""
    return "".join(ch for ch in str(name).upper() if ch.isalnum())


def find_col(df: pd.DataFrame, *candidates: str):
    """Return the first column in df matching any candidate (tolerant)."""
    lut = {norm(c): c for c in df.columns}
    for cand in candidates:
        c = lut.get(norm(cand))
        if c is not None:
            return c
    return None


def numcol(df: pd.DataFrame, col):
    """Numeric series for a (possibly missing) column; zeros if absent."""
    if col is None or col not in df.columns:
        return pd.Series(np.zeros(len(df)), index=df.index)
    return pd.to_numeric(df[col], errors="coerce").fillna(0)


def analyse_month(path: Path):
    """Run the four checks on one monthly file; return (summary_dict, frames_dict)."""
    fm = full_month_days(path.stem)
    df = pd.read_excel(path, sheet_name=0, header=0, engine="openpyxl")
    n = len(df)

    # --- resolve columns (tolerant to _ / space / case variants) -----------
    c_emp   = find_col(df, "EMPCODE", "EMP CODE")
    c_name  = find_col(df, "FULLNAME", "FULL NAME")
    c_state = find_col(df, "SITESTATE", "SITE STATE")
    c_site  = find_col(df, "SITENAME", "SITE NAME")
    c_rbas  = find_col(df, "REVISED_BASIC")
    c_rda   = find_col(df, "REVISED_DA")
    c_rpf   = find_col(df, "REVISED_PF")
    c_ecr   = find_col(df, "ECR_PF", "ECR PF")
    c_rgr   = find_col(df, "REVISED_GROSS", "REVISED_GROSS_NEW (final)", "REVISED_GROSS_NEW")
    c_resi  = find_col(df, "REVISED_ESIC")
    c_fut   = find_col(df, "ESIC AS PER FUTURE", "ESIC_AS_PER_FUTURE")
    c_adj   = find_col(df, "ADJ_WORKING_DAYS")
    c_gproj = find_col(df, "MONTHLY_GROSS_PROJECTION", "PROJECTED_GROSS_FULL_MONTH")

    rbas = numcol(df, c_rbas)
    rda  = numcol(df, c_rda)
    rpf  = numcol(df, c_rpf)
    ecr  = numcol(df, c_ecr)
    rgr  = numcol(df, c_rgr)
    resi = numcol(df, c_resi)
    adj  = numcol(df, c_adj)

    bd = rbas + rda

    # gross projection: prefer the file's column, else recompute
    if c_gproj is not None:
        gproj = numcol(df, c_gproj)
    else:
        gproj = pd.Series(np.where(adj > 0, rgr * fm / adj.replace(0, np.nan), 0),
                          index=df.index).fillna(0)
    # recomputed BD projection for the M6 view
    bdproj = pd.Series(np.where(adj > 0, bd * fm / adj.replace(0, np.nan), 0),
                       index=df.index).fillna(0)

    def ident(mask):
        cols = [c for c in (c_emp, c_name, c_state, c_site) if c is not None]
        out = df.loc[mask, cols].copy()
        return out

    # ---- CHECK 1: PF == 12% of (Basic+DA) on PF>0 rows --------------------
    pf_rows = rpf > 0
    pf_exp  = (PF_RATE * bd).round(2)
    pf_bad  = pf_rows & ((rpf - pf_exp).abs() > RUPEE_TOL)
    c1 = ident(pf_bad)
    if len(c1):
        c1["REVISED_PF"] = rpf[pf_bad].round(2).values
        c1["12%_of_BASIC+DA"] = pf_exp[pf_bad].values
        c1["DIFF"] = (rpf[pf_bad] - pf_exp[pf_bad]).round(2).values
        c1["BASIC+DA"] = bd[pf_bad].round(2).values

    # ---- CHECK 2: ECR PF present => Basic+DA < 15,000 (exceptions) --------
    ecr_rows = ecr > 0
    over_ceiling = ecr_rows & (bd > PF_CEILING + 0.5)        # static exception
    over_proj    = ecr_rows & (bdproj > PF_CEILING + 0.5)    # M6 full-month view
    c2 = ident(over_ceiling)
    if len(c2):
        c2["ECR_PF"] = ecr[over_ceiling].round(2).values
        c2["REVISED_PF"] = rpf[over_ceiling].round(2).values
        c2["BASIC+DA"] = bd[over_ceiling].round(2).values
        c2["BASIC+DA_full_month"] = bdproj[over_ceiling].round(0).values
        c2["ADJ_WORKING_DAYS"] = adj[over_ceiling].values

    # ---- CHECK 3a: ESI == 0.75% of gross on ESI>0 rows -------------------
    esi_rows = resi > 0
    esi_exp  = (ESI_RATE * rgr).round(2)
    esi_bad  = esi_rows & ((resi - esi_exp).abs() > RUPEE_TOL)
    c3a = ident(esi_bad)
    if len(c3a):
        c3a["REVISED_ESIC"] = resi[esi_bad].round(2).values
        c3a["0.75%_of_GROSS"] = esi_exp[esi_bad].values
        c3a["DIFF"] = (resi[esi_bad] - esi_exp[esi_bad]).round(2).values
        c3a["REVISED_GROSS"] = rgr[esi_bad].round(2).values

    # ---- CHECK 3b: ESI present => gross <= 21,000 (exceptions) -----------
    esi_over = esi_rows & (rgr > ESI_CEILING + 0.5)
    c3b = ident(esi_over)
    if len(c3b):
        c3b["REVISED_ESIC"] = resi[esi_over].round(2).values
        c3b["REVISED_GROSS"] = rgr[esi_over].round(2).values
        c3b["OVER_BY"] = (rgr[esi_over] - ESI_CEILING).round(2).values

    # ---- CHECK 4: full-month gross projection way too high ---------------
    high   = gproj > GROSS_PROJ_HIGH
    absurd = gproj > GROSS_PROJ_ABSURD
    c4 = ident(high)
    if len(c4):
        c4["REVISED_GROSS"] = rgr[high].round(2).values
        c4["ADJ_WORKING_DAYS"] = adj[high].values
        c4["FULL_MONTH_GROSS_PROJECTION"] = gproj[high].round(0).values
        c4 = c4.sort_values("FULL_MONTH_GROSS_PROJECTION", ascending=False)

    summary = {
        "Month": path.stem,
        "Rows": n,
        "Days_in_month": fm,
        "PF>0_rows": int(pf_rows.sum()),
        "C1_PF!=12%(B+D)": int(pf_bad.sum()),
        "ECR_PF>0_rows": int(ecr_rows.sum()),
        "C2_ECR&B+D>15000": int(over_ceiling.sum()),
        "C2_ECR&B+D_fullmonth>15000": int(over_proj.sum()),
        "ESI>0_rows": int(esi_rows.sum()),
        "C3a_ESI!=0.75%gross": int(esi_bad.sum()),
        "C3b_ESI&gross>21000": int(esi_over.sum()),
        "C4_grossproj>50k": int(high.sum()),
        "C4_grossproj>100k": int(absurd.sum()),
        "Max_gross_projection": float(gproj.max()) if n else 0.0,
    }
    frames = {
        "C1_PF_not_12pct": c1,
        "C2_ECR_BD_over_15000": c2,
        "C3a_ESI_not_075pct": c3a,
        "C3b_ESI_gross_over_21000": c3b,
        "C4_gross_proj_too_high": c4,
    }
    return summary, frames


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", help="folder containing monthly xlsx files (RECONCILED)")
    ap.add_argument("--out", help="optional path for an .xlsx report")
    args = ap.parse_args(argv)

    folder = Path(args.folder)
    files = []
    for m in MONTH_ORDER:
        for cand in (folder / f"{m}.xlsx", folder / f"{m}.XLSX"):
            if cand.exists():
                files.append(cand)
                break
    if not files:  # fall back to any xlsx
        files = sorted(folder.glob("*.xlsx"))
    if not files:
        sys.exit(f"No .xlsx files found in {folder}")

    summaries, all_frames = [], {}
    for f in files:
        print(f"\n=== {f.stem} ===")
        try:
            s, frames = analyse_month(f)
        except Exception as e:                       # noqa: BLE001
            print(f"  ERROR reading {f.name}: {e}")
            continue
        summaries.append(s)
        all_frames[f.stem] = frames
        print(f"  rows={s['Rows']:,}  days={s['Days_in_month']}")
        print(f"  CHECK 1  PF != 12%(Basic+DA)          : {s['C1_PF!=12%(B+D)']:>5}  "
              f"(of {s['PF>0_rows']:,} PF rows)")
        print(f"  CHECK 2  ECR PF set & Basic+DA>15,000 : {s['C2_ECR&B+D>15000']:>5}  "
              f"exceptions (full-month view: {s['C2_ECR&B+D_fullmonth>15000']:,})")
        print(f"  CHECK 3a ESI != 0.75%(gross)          : {s['C3a_ESI!=0.75%gross']:>5}  "
              f"(of {s['ESI>0_rows']:,} ESI rows)")
        print(f"  CHECK 3b ESI set & gross>21,000       : {s['C3b_ESI&gross>21000']:>5}  exceptions")
        print(f"  CHECK 4  full-month gross proj >50k   : {s['C4_grossproj>50k']:>5}  "
              f"(>100k: {s['C4_grossproj>100k']}, max Rs {s['Max_gross_projection']:,.0f})")

    sum_df = pd.DataFrame(summaries)
    print("\n================ CONSOLIDATED ================")
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(sum_df.to_string(index=False))

    if args.out:
        out = Path(args.out)
        with pd.ExcelWriter(out, engine="openpyxl") as xw:
            sum_df.to_excel(xw, sheet_name="Summary", index=False)
            for month, frames in all_frames.items():
                for key, fr in frames.items():
                    if fr is not None and len(fr):
                        sheet = f"{month[:10]}_{key.split('_')[0]}"[:31]
                        fr.to_excel(xw, sheet_name=sheet, index=False)
        print(f"\nReport written: {out}")


if __name__ == "__main__":
    main()
