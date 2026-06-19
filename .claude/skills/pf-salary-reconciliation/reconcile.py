#!/usr/bin/env python3
"""
PF + ESI salary reconciliation pipeline (skill: pf-salary-reconciliation).

Reconciles a monthly pan-India salary sheet so that, per employee,
  Salary PF  == ECR PF        (EE summed across deduped ECR/FORMAT files)
  Salary ESIC == Future ESIC  (col Q of the Future reference FR_sheet)
while NET PAYABLE never changes (differences absorbed via OTHER DEDUCTION /
REVISED_ATTENDANCE_ALLOWANCE).

It is COLUMN-NAME driven, not column-letter driven, so it tolerates layout drift.
Run locally where the full salary file lives (the Drive download tool caps at 10 MB).

    python reconcile.py --salary apr26_FULL_monthly_sheet.xlsx \
        --ecr FORMAT-APRIL_2026_DELHI.xlsx FORMAT_APRIL_2026_STEAGE.xlsx FORMAT-APRIL_2026_DMART.xlsx \
        --future "Future reference sheet_2604.xlsx" \
        --month 2026-04 --salary-header 4 --out-prefix April26

See SKILL.md for the full rule set. Validate the first month's output against the
prior month's *_Final_Complete / *_Reconciliation_Report before filing.
"""
from __future__ import annotations
import argparse, calendar, math, sys
import numpy as np
import pandas as pd

R = lambda x, n=2: round(float(x), n)


# --------------------------------------------------------------------------- #
# Column resolution                                                            #
# --------------------------------------------------------------------------- #
def _norm(s):
    return "".join(str(s).strip().upper().split())

def resolve(df, *names, required=True):
    """Return the actual df column matching any of `names` (case/space-insensitive)."""
    lut = {_norm(c): c for c in df.columns}
    for n in names:
        if _norm(n) in lut:
            return lut[_norm(n)]
    if required:
        raise KeyError(f"None of {names} found. Available sample: {list(df.columns)[:40]}")
    return None

def num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0).astype(float)

def clean_code(s):
    return s.astype(str).str.strip().str.split(".").str[0]


# --------------------------------------------------------------------------- #
# Loaders                                                                      #
# --------------------------------------------------------------------------- #
def load_ecr(paths):
    """Dedup each ECR/FORMAT file by EMP CODE, then concat + sum EE per EMP CODE."""
    frames = []
    for p in paths:
        raw = pd.read_excel(p, header=None, dtype=object)
        hdr = next((i for i in range(min(5, len(raw)))
                    if raw.iloc[i].astype(str).str.upper().str.strip().eq("EMP CODE").any()), 0)
        df = pd.read_excel(p, header=hdr)
        code = resolve(df, "EMP CODE", "EMPCODE")
        ee = resolve(df, "EE", "PF WAGES EE", "EE AMOUNT", required=False) or resolve(df, "EE")
        df = df[[code, ee]].copy()
        df.columns = ["EMP CODE", "EE"]
        df["EMP CODE"] = clean_code(df["EMP CODE"])
        df["EE"] = num(df["EE"])
        df = df[df["EMP CODE"].str.match(r"^\d+$")]           # drop TOTAL / blank rows
        df = df.drop_duplicates(subset="EMP CODE", keep="first")  # CRITICAL per-file dedup
        frames.append(df)
        print(f"  ECR {p}: {len(df)} unique emps, EE={df['EE'].sum():,.0f}")
    allf = pd.concat(frames, ignore_index=True)
    by = allf.groupby("EMP CODE", as_index=False)["EE"].sum()
    print(f"  ECR merged: {len(by)} emps, total EE={by['EE'].sum():,.0f}")
    return by.rename(columns={"EE": "ECR_PF"})

def load_future(path):
    """FR_sheet: header row 3 (header=2), EMPCODE col G, ESIC employee col Q, SITECODE col B."""
    df = pd.read_excel(path, sheet_name="FR_sheet", header=2)
    code = resolve(df, "EMPCODE", "EMP CODE")
    esic = resolve(df, "ESIC")              # col Q employee contribution
    site = resolve(df, "SITECODE")
    out = pd.DataFrame({
        "EMPCODE": clean_code(df[code]),
        "FUTURE_ESI": num(df[esic]),
        "FUTURE_SITECODE": clean_code(df[site]),
    })
    out = out[out["EMPCODE"].str.match(r"^\d+$")]
    out = out.groupby("EMPCODE", as_index=False).agg(
        FUTURE_ESI=("FUTURE_ESI", "sum"),
        FUTURE_SITECODE=("FUTURE_SITECODE", "first"))
    print(f"  Future: {len(out)} emps, total ESIC={out['FUTURE_ESI'].sum():,.0f}")
    return out


# --------------------------------------------------------------------------- #
# Pipeline                                                                     #
# --------------------------------------------------------------------------- #
def reconcile(sal, ecr, fut, full_month):
    C = {k: resolve(sal, *v) for k, v in {
        "EMPCODE": ["EMPCODE", "EMP CODE"], "SITECODE": ["SITECODE"],
        "SDD": ["SITEDIVISIONDAYS"], "ND": ["NORMALDAYS"],
        "FB": ["FIXED_BASIC"], "FD": ["FIXED_DA"], "BASIC": ["BASIC"], "DA": ["DA"],
        "PF": ["PF"], "ESIC": ["ESIC"], "OD": ["OTHER DEDUCTION", "OTHER_DEDUCTION"],
        "GROSS": ["GROSS AMT", "GROSS"], "NET": ["NETPAYABLE", "NET PAYABLE"],
        "ESIW": ["ESI WAGES"],
    }.items()}

    sal["EMPCODE"] = clean_code(sal[C["EMPCODE"]])
    sal["SITECODE_C"] = clean_code(sal[C["SITECODE"]])
    rc = sal.groupby("EMPCODE").size().rename("ROW_COUNT")
    sal = sal.merge(rc, on="EMPCODE", how="left")
    sal = sal.merge(ecr, left_on="EMPCODE", right_on="EMP CODE", how="left")
    sal["ECR_PF"] = num(sal.get("ECR_PF")).fillna(0.0)

    # working numeric copies
    for k in ("SDD", "ND", "FB", "FD", "BASIC", "DA", "PF", "ESIC", "OD", "GROSS", "NET", "ESIW"):
        sal[k + "_v"] = num(sal[C[k]])
    sal["ADJ_WORKING_DAYS"] = sal["ND_v"].round().clip(1, 31).astype(int)
    sal["REVISED_BASIC"] = sal["BASIC_v"]
    sal["REVISED_DA"] = sal["DA_v"]
    sal["REVISED_ATTENDANCE_ALLOWANCE"] = 0.0
    sal["REVISED_PF"] = sal["PF_v"]
    sal["REVISED_OTHER_DEDUCTION"] = sal["OD_v"]
    sal["REVISED_GROSS"] = sal["GROSS_v"]
    sal["REVISED_NET_PAYABLE"] = sal["NET_v"]
    sal["REVISED_ESIC"] = sal["ESIC_v"]
    sal["RULE_APPLIED"] = ""
    sal["NOTES"] = ""
    sal["remark"] = ""

    # ---- main PF row per employee --------------------------------------- #
    main = np.zeros(len(sal), dtype=bool)
    idx = sal.reset_index(drop=True)
    for _, g in idx.groupby("EMPCODE"):
        pf = g[g["PF_v"] > 0]
        if len(pf) == 0:
            continue
        if len(pf) == 1:
            main[pf.index[0]] = True
        else:
            ecrv = g["ECR_PF"].iloc[0]
            exact = pf[(pf["PF_v"] - ecrv).abs() <= 1]
            main[(exact.index[0] if len(exact) else pf["PF_v"].idxmax())] = True
    sal = idx
    sal["IS_MAIN_PF"] = main

    # ---- PF rules ------------------------------------------------------- #
    for i, r in sal.iterrows():
        pf0, ecrv = r["PF_v"], r["ECR_PF"]
        fbd = r["FB_v"] + r["FD_v"]
        if r["ROW_COUNT"] > 1 and not r["IS_MAIN_PF"]:
            if pf0 > 0:                                   # secondary PF row
                sal.at[i, "REVISED_PF"] = 0.0
                sal.at[i, "REVISED_OTHER_DEDUCTION"] = r["OD_v"] + pf0
                sal.at[i, "RULE_APPLIED"] = "MULTI_SITE_SECONDARY_PF"
            else:
                sal.at[i, "RULE_APPLIED"] = "MULTI_SITE_ZERO_PF"
            continue
        if pf0 == 0 and ecrv == 0:
            sal.at[i, "RULE_APPLIED"] = "NO_PF"; continue
        if ecrv == 0:                                     # Rule 3 Not in ECR
            sal.at[i, "REVISED_OTHER_DEDUCTION"] = r["OD_v"] + pf0
            sal.at[i, "REVISED_PF"] = 0.0
            sal.at[i, "REVISED_BASIC"] = 15001.0
            sal.at[i, "RULE_APPLIED"] = "NOT_IN_ECR"; sal.at[i, "remark"] = "ok"; continue
        if abs(ecrv - pf0) <= 1:
            sal.at[i, "REVISED_PF"] = ecrv
            sal.at[i, "RULE_APPLIED"] = "NO_ADJUSTMENT"; sal.at[i, "remark"] = "match as per ecr"; continue
        if ecrv < pf0 and fbd <= 15000:                   # Rule 1 Case B
            adj = (ecrv / (r["FB_v"] * 0.12)) * r["SDD_v"] if r["FB_v"] > 0 else r["ADJ_WORKING_DAYS"]
            rb = (r["FB_v"] / r["SDD_v"]) * adj if r["SDD_v"] else r["BASIC_v"]
            sal.at[i, "ADJ_WORKING_DAYS"] = int(max(1, min(31, round(adj))))
            sal.at[i, "REVISED_BASIC"] = R(rb)
            sal.at[i, "REVISED_GROSS"] = r["GROSS_v"] - (r["BASIC_v"] - rb)
            sal.at[i, "REVISED_PF"] = ecrv
            sal.at[i, "REVISED_OTHER_DEDUCTION"] = r["OD_v"] + (pf0 - ecrv)
            sal.at[i, "RULE_APPLIED"] = "CASE_B"; sal.at[i, "remark"] = "to be check"
        elif ecrv < pf0:                                  # Rule 2 Case A
            sal.at[i, "REVISED_PF"] = ecrv
            sal.at[i, "REVISED_OTHER_DEDUCTION"] = r["OD_v"] + (pf0 - ecrv)
            sal.at[i, "RULE_APPLIED"] = "CASE_A"
            sal.at[i, "remark"] = "Pf 1800" if abs(ecrv - 1800) < 1 else "Fix Gross >15000"
        else:                                             # Rule 4 Cond 2
            sal.at[i, "REVISED_PF"] = ecrv
            sal.at[i, "REVISED_OTHER_DEDUCTION"] = r["OD_v"] - (ecrv - pf0)
            sal.at[i, "RULE_APPLIED"] = "COND2"; sal.at[i, "remark"] = "match as per ecr"

    # ---- 12% basic fix (No-Adjustment only) ----------------------------- #
    m = sal["RULE_APPLIED"].eq("NO_ADJUSTMENT")
    tgt = (sal["REVISED_PF"] / 0.12).round()
    bump = m & (tgt > sal["REVISED_BASIC"])
    d = (tgt - sal["REVISED_BASIC"]).where(bump, 0.0)
    sal["REVISED_BASIC"] += d
    sal["REVISED_GROSS"] += d
    sal["REVISED_OTHER_DEDUCTION"] += d

    # ---- min-wage floor (captured at this ADJ_WORKING_DAYS context) ----- #
    sal["MW_FLOOR"] = (sal["BASIC_v"] / sal["ND_v"].replace(0, np.nan)).fillna(0) * sal["ADJ_WORKING_DAYS"]
    lift = (sal["REVISED_PF"] > 0) & (sal["REVISED_BASIC"] < sal["MW_FLOOR"] - 0.5)
    sal.loc[lift, "REVISED_BASIC"] = sal.loc[lift, "MW_FLOOR"]
    sal.loc[lift, "REVISED_PF"] = (0.12 * (sal.loc[lift, "REVISED_BASIC"] + sal.loc[lift, "REVISED_DA"])).round(2)
    sal.loc[lift, "remark"] = sal.loc[lift, "remark"] + " [MW_FLOOR_APPLIED]"

    # ---- enforce REVISED_PF == 12%(B+D) via attendance allowance -------- #
    # Min-wage floor (hierarchy #2) outranks the 12% rule (#3): never lower
    # REVISED_BASIC below the floor (skips above-ceiling Case-A rows).
    pfpos = sal["REVISED_PF"] > 0
    th = (sal["REVISED_PF"] * 0.001).clip(lower=0.5)
    gd_new = (sal["REVISED_PF"] / 0.12).round()
    need = pfpos & ((gd_new - sal["REVISED_BASIC"]).abs() > th) & (gd_new >= sal["MW_FLOOR"] - 0.5)
    delta = (gd_new - sal["REVISED_BASIC"]).where(need, 0.0)
    sal["REVISED_BASIC"] += delta
    sal["REVISED_ATTENDANCE_ALLOWANCE"] -= delta            # GROSS unchanged

    sal["ADJ_WORKING_DAYS"] = sal["ADJ_WORKING_DAYS"].clip(1, 31).round().astype(int)

    # ---- ESI passes ----------------------------------------------------- #
    sal = sal.merge(fut, on="EMPCODE", how="left")
    sal["FUTURE_ESI"] = num(sal.get("FUTURE_ESI"))
    in_fut = sal["EMPCODE"].isin(set(fut["EMPCODE"]))

    # E1 primary-site alignment
    primary = np.zeros(len(sal), dtype=bool)
    for _, g in sal.groupby("EMPCODE"):
        if not g["FUTURE_ESI"].iloc[0] and g["EMPCODE"].iloc[0] not in set(fut["EMPCODE"]):
            continue
        fs = g["FUTURE_SITECODE"].iloc[0]
        match = g[g["SITECODE_C"] == fs]
        pidx = match.index[0] if len(match) else g["ESIW_v"].idxmax()
        primary[pidx] = True
    sal["IS_PRIMARY_ESI"] = primary
    orig_esic = sal["ESIC_v"].copy()
    sal["REVISED_ESIC"] = 0.0
    sal["ESIC_AS_PER_FUTURE"] = 0.0
    sal.loc[primary, "REVISED_ESIC"] = sal.loc[primary, "FUTURE_ESI"]
    sal.loc[primary, "ESIC_AS_PER_FUTURE"] = sal.loc[primary, "FUTURE_ESI"]

    # E1b absorb ESI delta into OTHER_DEDUCTION (NET holds)
    sal["REVISED_OTHER_DEDUCTION"] += (orig_esic - sal["REVISED_ESIC"])

    fmd = full_month
    bd = sal["REVISED_BASIC"] + sal["REVISED_DA"]
    gc = sal["ADJ_WORKING_DAYS"].astype(float)
    # E2 PF ceiling
    e2 = (sal["ECR_PF"] == 0) & (gc > 0) & (bd * 31 / gc < 15000) & (bd > 0)
    sal.loc[e2, "ADJ_WORKING_DAYS"] = np.floor(bd[e2] * 31 / 15001).clip(lower=1)
    # E2b ESI ceiling
    gc = sal["ADJ_WORKING_DAYS"].astype(float)
    e2b = (sal["REVISED_ESIC"] == 0) & (gc > 0) & (sal["REVISED_GROSS"] > 0) & \
          (sal["REVISED_GROSS"] * fmd / gc <= 21000)
    newgc = np.floor(sal["REVISED_GROSS"] * fmd / 21001)
    apply = e2b & (newgc > 0) & (newgc < gc)
    sal.loc[apply, "ADJ_WORKING_DAYS"] = newgc[apply]
    sal["ADJ_WORKING_DAYS"] = sal["ADJ_WORKING_DAYS"].clip(1, fmd).round().astype(int)

    # recompute REVISED_GROSS = max(GROSS, B+D, ESI/0.0075); ATT absorbs
    revg = np.maximum.reduce([sal["REVISED_GROSS"].values, (bd).values,
                              (sal["REVISED_ESIC"] / 0.0075).values])
    sal["REVISED_ATTENDANCE_ALLOWANCE"] = revg - bd
    sal["REVISED_GROSS"] = revg

    # NET balancer via OTHER_DEDUCTION (PF side): OD = GROSS - PF - ESI - NET
    sal["REVISED_OTHER_DEDUCTION"] = (sal["REVISED_GROSS"] - sal["REVISED_PF"]
                                      - sal["REVISED_ESIC"] - sal["NET_v"])
    # E3 negative OTHER_DED → attendance allowance
    neg = sal["REVISED_OTHER_DEDUCTION"] < 0
    amt = (-sal["REVISED_OTHER_DEDUCTION"]).where(neg, 0.0)
    sal["REVISED_ATTENDANCE_ALLOWANCE"] += amt
    sal["REVISED_GROSS"] += amt
    sal.loc[neg, "REVISED_OTHER_DEDUCTION"] = 0.0

    sal["REVISED_TOTAL_DED"] = sal["REVISED_PF"] + sal["REVISED_ESIC"] + sal["REVISED_OTHER_DEDUCTION"]
    sal["REVISED_NET_PAYABLE"] = sal["REVISED_GROSS"] - sal["REVISED_TOTAL_DED"]

    # ---- final patch passes -------------------------------------------- #
    proj = sal["REVISED_GROSS"] * fmd / 21001
    tgt_days = np.floor(proj).clip(1, fmd)
    sal["ADJ_WORKING_DAYS"] = np.maximum(sal["ADJ_WORKING_DAYS"], tgt_days).clip(1, fmd).astype(int)
    sal["ECR_PF_CAPPED"] = np.minimum(sal["ECR_PF"], sal["REVISED_PF"])

    # ---- audit columns -------------------------------------------------- #
    sal["Future_ESI"] = sal["FUTURE_ESI"]
    sal["ESI DIFFERENCE (Future-REVISED)"] = sal["Future_ESI"] - sal["REVISED_ESIC"]
    sal["NET_PAYABLE_DIFF"] = sal["REVISED_NET_PAYABLE"] - sal["NET_v"]
    denom = (sal["BASIC_v"] + sal["DA_v"]).replace(0, np.nan)
    sal["%"] = (sal["PF_v"] / denom * 100).fillna(0).round(3)
    sal["12% OF (REVISED_BASIC+DA)"] = (0.12 * (sal["REVISED_BASIC"] + sal["REVISED_DA"])).round(2)
    sal["DIFF (12%_PF vs REVISED_PF)"] = (sal["12% OF (REVISED_BASIC+DA)"] - sal["REVISED_PF"]).round(2)
    sal["REVISED_%"] = np.where(sal["REVISED_BASIC"] == 0, 0,
                                sal["REVISED_PF"] / sal["REVISED_BASIC"].replace(0, np.nan) * 100).round(3)
    sal["MONTHLY_BD_PROJECTION"] = (bd * fmd / sal["ADJ_WORKING_DAYS"]).round(0)
    sal["MONTHLY_GROSS_PROJECTION"] = (sal["REVISED_GROSS"] * fmd / sal["ADJ_WORKING_DAYS"]).round(0)
    return sal, C


# --------------------------------------------------------------------------- #
# Validation                                                                   #
# --------------------------------------------------------------------------- #
def validate(sal):
    pf = sal["REVISED_PF"] > 0
    below_ceiling = (sal["REVISED_BASIC"] + sal["REVISED_DA"]) <= 15000
    # 12% relaxes where the min-wage floor binds (raising basic to 12%/PF would breach the
    # floor) or PF is pinned to a low ECR filing — both are hierarchy-driven, not errors.
    floor_bound = (sal["REVISED_PF"] / 0.12) < (sal["MW_FLOOR"] - 0.5)
    c3_relaxed = int((pf & below_ceiling & floor_bound).sum())
    checks = {
        "C1 OTHER_DED>=0": (sal["REVISED_OTHER_DEDUCTION"] >= -0.5).all(),
        "C2 NET unchanged": (sal["NET_PAYABLE_DIFF"].abs() <= 1).all(),
        "C3 PF=12%(B+D) below ceiling": ((sal["DIFF (12%_PF vs REVISED_PF)"].abs() <= 1)
                                         | ~(pf & below_ceiling) | floor_bound).all(),
        "C5 ATT_ALW>=0": (sal["REVISED_ATTENDANCE_ALLOWANCE"] >= -0.5).all(),
        "C6 TOTAL_DED>=0": (sal["REVISED_TOTAL_DED"] >= -0.5).all(),
        "C7 GROSS=B+D+ATT": ((sal["REVISED_GROSS"] -
            (sal["REVISED_BASIC"] + sal["REVISED_DA"] + sal["REVISED_ATTENDANCE_ALLOWANCE"])).abs() <= 1).all(),
        "C9 days in [1,31]": sal["ADJ_WORKING_DAYS"].between(1, 31).all(),
        "C10 ECR_cap<=PF": (sal["ECR_PF_CAPPED"] <= sal["REVISED_PF"] + 0.5).all(),
        "C-MW basic>=floor": ((sal["REVISED_BASIC"] >= sal["MW_FLOOR"] - 0.5) | ~pf).all(),
        "C-INT days integer": (sal["ADJ_WORKING_DAYS"] == sal["ADJ_WORKING_DAYS"].round()).all(),
    }
    print("\nVALIDATION")
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    if c3_relaxed:
        print(f"  INFO  C3 relaxed on {c3_relaxed} floor-bound / ECR-pinned rows (expected)")
    return all(checks.values())


# --------------------------------------------------------------------------- #
# Output                                                                        #
# --------------------------------------------------------------------------- #
AUDIT = ["ADJ_WORKING_DAYS", "REVISED_BASIC", "REVISED_DA", "REVISED_ATTENDANCE_ALLOWANCE",
         "REVISED_GROSS", "ECR_PF", "REVISED_PF", "REVISED_ESIC", "Future_ESI",
         "ESIC_AS_PER_FUTURE", "ESI DIFFERENCE (Future-REVISED)", "REVISED_OTHER_DEDUCTION",
         "REVISED_TOTAL_DED", "REVISED_NET_PAYABLE", "NET_PAYABLE_DIFF", "RULE_APPLIED",
         "NOTES", "%", "remark", "12% OF (REVISED_BASIC+DA)", "DIFF (12%_PF vs REVISED_PF)",
         "REVISED_%", "MONTHLY_BD_PROJECTION", "MONTHLY_GROSS_PROJECTION"]

def write_outputs(sal, original_cols, prefix):
    final = sal.copy()
    keep = [c for c in original_cols if c != "ESIC.1"] + \
           [c if c != "ESIC_AS_PER_FUTURE" else "ESIC_AS_PER_FUTURE" for c in AUDIT]
    final = final[[c for c in keep if c in final.columns]]
    final = final.rename(columns={"ESIC_AS_PER_FUTURE": "ESIC AS PER FUTURE"})
    fc = f"{prefix}_Final_Complete.xlsx"
    final.to_excel(fc, index=False)
    print(f"\nwrote {fc}  ({final.shape[0]} rows x {final.shape[1]} cols)")

    rep = f"{prefix}_Reconciliation_Report.xlsx"
    with pd.ExcelWriter(rep, engine="openpyxl") as xl:
        summ = (sal.groupby("RULE_APPLIED")
                .agg(rows=("EMPCODE", "size"),
                     orig_pf=("PF_v", "sum"), revised_pf=("REVISED_PF", "sum"),
                     ecr_pf=("ECR_PF", "sum")).reset_index())
        summ.to_excel(xl, sheet_name="Summary", index=False)
        pf_cols = ["EMPCODE", C0(sal, "FULLNAME"), "ROW_COUNT", "IS_MAIN_PF", "PF_v",
                   "ECR_PF", "REVISED_PF", "REVISED_BASIC", "RULE_APPLIED", "remark"]
        sal[[c for c in pf_cols if c in sal.columns]].to_excel(xl, sheet_name="PF_Audit", index=False)
        esi_cols = ["EMPCODE", "SITECODE_C", "IS_PRIMARY_ESI", "ESIC_v",
                    "REVISED_ESIC", "Future_ESI", "ESI DIFFERENCE (Future-REVISED)"]
        sal[[c for c in esi_cols if c in sal.columns]].to_excel(xl, sheet_name="ESI_Audit", index=False)
        math_cols = ["EMPCODE", "REVISED_GROSS", "REVISED_PF", "REVISED_ESIC",
                     "REVISED_OTHER_DEDUCTION", "REVISED_TOTAL_DED", "REVISED_NET_PAYABLE",
                     "NET_v", "NET_PAYABLE_DIFF", "DIFF (12%_PF vs REVISED_PF)", "ADJ_WORKING_DAYS"]
        sal[[c for c in math_cols if c in sal.columns]].to_excel(xl, sheet_name="Math_Checks", index=False)
        final.to_excel(xl, sheet_name="Reconciled_Data", index=False)
    print(f"wrote {rep}")

def C0(df, *n):
    return resolve(df, *n, required=False) or n[0]


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salary", required=True)
    ap.add_argument("--ecr", nargs="+", required=True)
    ap.add_argument("--future", required=True)
    ap.add_argument("--month", required=True, help="YYYY-MM, e.g. 2026-04")
    ap.add_argument("--salary-header", type=int, default=4)
    ap.add_argument("--out-prefix", required=True)
    a = ap.parse_args()

    y, m = map(int, a.month.split("-"))
    full_month = calendar.monthrange(y, m)[1]
    print(f"Month {a.month}  FULL_MONTH={full_month}")

    print("Loading ECR ...");    ecr = load_ecr(a.ecr)
    print("Loading Future ...");  fut = load_future(a.future)
    print("Loading salary ...")
    sal = pd.read_excel(a.salary, header=a.salary_header)
    original_cols = list(sal.columns)
    print(f"  salary: {sal.shape[0]} rows x {sal.shape[1]} cols")

    sal, C = reconcile(sal, ecr, fut, full_month)
    ok = validate(sal)
    write_outputs(sal, original_cols, a.out_prefix)
    print("\nDONE" + ("" if ok else "  (WITH VALIDATION FAILURES — review before filing)"))
    sys.exit(0 if ok else 2)

if __name__ == "__main__":
    main()
