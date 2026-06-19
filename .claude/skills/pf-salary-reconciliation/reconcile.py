#!/usr/bin/env python3
"""
PF + ESI salary reconciliation pipeline (skill: pf-salary-reconciliation).

Implements the v3 strict single-pass lock-in + v4 field rules (M1-M6) from
PF_SALARY_RECONCILIATION_SKILL_v4.md — the methodology used for the 2025-26
monthly closes. Per employee/row the filed sheet is locked so that:
  - REVISED_PF   == ECR_PF                          (anchor)
  - REVISED_ESIC == ESIC as per Future              (anchor)
  - REVISED_PF   == 12% x (REVISED_BASIC+REVISED_DA) (statutory, exact)
  - REVISED_ESIC == 0.75% x REVISED_GROSS           (relaxed UP only when forced)
  - REVISED_NET_PAYABLE == NETPAYABLE               (sacrosanct)
  - attendance allowance & OTHER_DEDUCTION >= 0      (by construction)
  - PF<=1800, ESI off >21k, BD/GROSS month-projections within ceilings (days tinker)

Column-name driven. Run locally where the full salary file lives.

    python reconcile.py --salary apr26_FULL_monthly_sheet.xlsx \
        --ecr FORMAT-APRIL_2026_DELHI.xlsx FORMAT_APRIL_2026_STEAGE.xlsx FORMAT-APRIL_2026_DMART.xlsx \
        --future "ESIC_CONSOLIDATED_APR_2026.xlsx" --month 2026-04 --out-prefix April26
"""
from __future__ import annotations
import argparse, calendar, sys
import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# Helpers / loaders                                                            #
# --------------------------------------------------------------------------- #
def _norm(s):
    return "".join(str(s).strip().upper().split())

def resolve(df, *names, required=True):
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

def detect_salary_header(path, maxscan=12):
    raw = pd.read_excel(path, header=None, nrows=maxscan, dtype=object)
    want = {_norm(x) for x in ("EMPCODE", "EMP CODE", "FULLNAME", "NETPAYABLE")}
    for i in range(len(raw)):
        if {_norm(c) for c in raw.iloc[i].tolist()} & want:
            return i
    return 0

def load_ecr(paths):
    """Dedup each ECR/FORMAT file by EMP CODE, then concat + sum EE per EMP CODE."""
    frames = []
    for p in paths:
        raw = pd.read_excel(p, header=None, dtype=object)
        hdr = next((i for i in range(min(5, len(raw)))
                    if raw.iloc[i].astype(str).str.upper().str.strip().eq("EMP CODE").any()), 0)
        df = pd.read_excel(p, header=hdr)
        code, ee = resolve(df, "EMP CODE", "EMPCODE"), resolve(df, "EE")
        df = df[[code, ee]].copy(); df.columns = ["EMP CODE", "EE"]
        df["EMP CODE"] = clean_code(df["EMP CODE"]); df["EE"] = num(df["EE"])
        df = df[df["EMP CODE"].str.match(r"^\d+$")].drop_duplicates("EMP CODE", keep="first")
        frames.append(df)
        print(f"  ECR {p}: {len(df)} unique emps, EE={df['EE'].sum():,.0f}")
    by = pd.concat(frames, ignore_index=True).groupby("EMP CODE", as_index=False)["EE"].sum()
    print(f"  ECR merged: {len(by)} emps, total EE={by['EE'].sum():,.0f}")
    return by.rename(columns={"EE": "ECR_PF"})

def load_future(path):
    df = pd.read_excel(path, sheet_name="FR_sheet", header=2)
    out = pd.DataFrame({
        "EMPCODE": clean_code(df[resolve(df, "EMPCODE", "EMP CODE")]),
        "FUTURE_ESI": num(df[resolve(df, "ESIC")]),
        "FUTURE_SITECODE": clean_code(df[resolve(df, "SITECODE")]),
    })
    out = out[out["EMPCODE"].str.match(r"^\d+$")]
    out = out.groupby("EMPCODE", as_index=False).agg(
        FUTURE_ESI=("FUTURE_ESI", "sum"), FUTURE_SITECODE=("FUTURE_SITECODE", "first"))
    print(f"  Future: {len(out)} emps, total ESIC={out['FUTURE_ESI'].sum():,.0f}")
    return out


# --------------------------------------------------------------------------- #
# v3 / v4 reconciliation                                                       #
# --------------------------------------------------------------------------- #
def reconcile(sal, ecr, fut, fmd):
    C = {k: resolve(sal, *v) for k, v in {
        "EMPCODE": ["EMPCODE", "EMP CODE"], "SITECODE": ["SITECODE"],
        "ND": ["NORMALDAYS"], "B": ["BASIC"], "DA": ["DA"], "ESIW": ["ESI WAGES"],
        "GROSS": ["GROSS AMT", "GROSS"], "NET": ["NETPAYABLE", "NET PAYABLE"],
    }.items()}
    sal["EMPCODE"] = clean_code(sal[C["EMPCODE"]])
    sal["SITECODE_C"] = clean_code(sal[C["SITECODE"]])
    for k in ("ND", "B", "DA", "ESIW", "GROSS", "NET"):
        sal[k + "_v"] = num(sal[C[k]])

    # employee-level anchors
    sal["ECR_PF"] = num(sal["EMPCODE"].map(dict(zip(ecr["EMP CODE"].astype(str), ecr["ECR_PF"]))))
    futc = fut["EMPCODE"].astype(str)
    sal["FUTURE_ESI"] = num(sal["EMPCODE"].map(dict(zip(futc, fut["FUTURE_ESI"]))))
    sal["FUTURE_SITECODE"] = sal["EMPCODE"].map(dict(zip(futc, fut["FUTURE_SITECODE"]))).fillna("")
    emp_in_pf = sal["ECR_PF"] > 0
    emp_in_esi = sal["EMPCODE"].isin(set(futc))

    # M1: PF anchored on the employee's MAX-NORMALDAYS row
    sal["REVISED_PF"] = 0.0
    sal["IS_MAIN_PF"] = False
    if emp_in_pf.any():
        midx = sal[emp_in_pf].groupby("EMPCODE")["ND_v"].idxmax()
        sal.loc[midx, "IS_MAIN_PF"] = True
        sal.loc[midx, "REVISED_PF"] = sal.loc[midx, "ECR_PF"]

    # ESI anchored on primary site row (sitecode match else max ESI wages)
    sal["REVISED_ESIC"] = 0.0
    sal["IS_PRIMARY_ESI"] = False
    for emp, grp in sal[emp_in_esi].groupby("EMPCODE"):
        fs = grp["FUTURE_SITECODE"].iloc[0]
        m = grp[grp["SITECODE_C"] == fs]
        pidx = m.index[0] if len(m) else grp["ESIW_v"].idxmax()
        sal.loc[pidx, "IS_PRIMARY_ESI"] = True
        sal.loc[pidx, "REVISED_ESIC"] = grp["FUTURE_ESI"].iloc[0]

    pf, esi, np_ = sal["REVISED_PF"].values, sal["REVISED_ESIC"].values, sal["NET_v"].values
    obasic, oda, ogross = sal["B_v"].values, sal["DA_v"].values, sal["GROSS_v"].values

    # ---- v3 core (per row, vectorised) --------------------------------- #
    BD_target = np.where(pf > 0, np.round(pf / 0.12), obasic + oda)
    GROSS_a = np.where(esi > 0, np.round(esi / 0.0075), ogross)
    GROSS_c = np_ + pf + esi
    new_GROSS = np.maximum.reduce([GROSS_a, BD_target, GROSS_c])
    new_DA = np.minimum(oda, BD_target)
    new_BASIC = BD_target - new_DA
    sal["REVISED_BASIC"] = new_BASIC
    sal["REVISED_DA"] = new_DA
    sal["REVISED_GROSS"] = new_GROSS
    sal["REVISED_ATTENDANCE_ALLOWANCE"] = new_GROSS - BD_target
    sal["REVISED_TOTAL_DED"] = new_GROSS - np_
    sal["REVISED_OTHER_DEDUCTION"] = (new_GROSS - np_) - pf - esi
    sal["RULE_075_RELAXED"] = (esi > 0) & (new_GROSS > GROSS_a + 1)

    # ---- M2 caps ------------------------------------------------------- #
    cap = sal["REVISED_PF"] > 1800                                   # PF <= 1800
    if cap.any():
        d_pf = sal["REVISED_PF"] - 1800
        d_b = sal["REVISED_BASIC"] - (15000 - sal["REVISED_DA"])
        sal.loc[cap, "REVISED_PF"] = 1800
        sal.loc[cap, "REVISED_BASIC"] = 15000 - sal.loc[cap, "REVISED_DA"]
        sal.loc[cap, "REVISED_ATTENDANCE_ALLOWANCE"] += d_b[cap]
        sal.loc[cap, "REVISED_OTHER_DEDUCTION"] += d_pf[cap]
    sal["ECR_PF_CAPPED"] = np.minimum(sal["ECR_PF"], sal["REVISED_PF"])
    ecap = (sal["REVISED_ESIC"] > 0) & (sal["REVISED_GROSS"] >= 21001)  # ESI off above ceiling
    sal.loc[ecap, "REVISED_OTHER_DEDUCTION"] += sal.loc[ecap, "REVISED_ESIC"]
    sal.loc[ecap, "REVISED_ESIC"] = 0.0

    # ---- M3/M6 day adjustment (feasible range, employee-level) --------- #
    bd = (sal["REVISED_BASIC"] + sal["REVISED_DA"]).values
    gr = sal["REVISED_GROSS"].values
    lo = np.ones(len(sal)); hi = np.full(len(sal), float(fmd))
    ip, ie = emp_in_pf.values, emp_in_esi.values
    lo = np.where(ip & (bd > 0), np.maximum(lo, np.ceil(bd * fmd / 15000)), lo)      # P1
    lo = np.where(ie & (gr > 0), np.maximum(lo, np.ceil(gr * fmd / 21000)), lo)      # P3
    hi = np.where((~ip) & (bd > 0), np.minimum(hi, np.floor(bd * fmd / 15001)), hi)  # P2
    hi = np.where((~ie) & (gr > 0), np.minimum(hi, np.floor(gr * fmd / 21001)), hi)  # P4
    dc = sal["ND_v"].round().clip(1, fmd).values
    nd = np.where(lo > hi, np.minimum(fmd, np.maximum(1, lo)),
                  np.where(dc < lo, lo, np.where(dc > hi, hi, dc)))
    sal["ADJ_WORKING_DAYS"] = np.clip(np.round(nd), 1, fmd).astype(int)

    # ---- M4a: non-ESI rows whose projection can't exceed 21k at max days -> lift GROSS
    adj = sal["ADJ_WORKING_DAYS"].values
    proj_gr = gr * fmd / adj
    m4a = (~ie) & (gr > 0) & (proj_gr <= 21000) & (adj >= fmd)
    if m4a.any():
        newg = np.ceil(21001 * adj / fmd)
        d = (newg - sal["REVISED_GROSS"].values)
        sal.loc[m4a, "REVISED_GROSS"] = newg[m4a]
        sal.loc[m4a, "REVISED_ATTENDANCE_ALLOWANCE"] += d[m4a]
        sal.loc[m4a, "REVISED_OTHER_DEDUCTION"] += d[m4a]
        sal.loc[m4a, "REVISED_TOTAL_DED"] += d[m4a]

    # ---- M4b: non-PF rows whose B+D projection can't exceed 15k at max days -> lift BASIC
    bd2 = (sal["REVISED_BASIC"] + sal["REVISED_DA"]).values
    proj_bd = bd2 * fmd / adj
    m4b = (~ip) & (bd2 > 0) & (proj_bd <= 15000) & (adj >= fmd)
    if m4b.any():
        tgt = np.ceil(15001 * adj / fmd)
        d = tgt - bd2
        att = sal["REVISED_ATTENDANCE_ALLOWANCE"].values
        room = m4b & (att >= d)
        sal.loc[room, "REVISED_BASIC"] += d[room]
        sal.loc[room, "REVISED_ATTENDANCE_ALLOWANCE"] -= d[room]
        nr = m4b & (att < d)
        sal.loc[nr, "REVISED_BASIC"] += d[nr]
        sal.loc[nr, "REVISED_GROSS"] += d[nr]
        sal.loc[nr, "REVISED_OTHER_DEDUCTION"] += d[nr]
        sal.loc[nr, "REVISED_TOTAL_DED"] += d[nr]

    # ---- M5 negative-plug cleanup -------------------------------------- #
    negA = sal["REVISED_ATTENDANCE_ALLOWANCE"] < -0.5
    if negA.any():
        df_ = -sal["REVISED_ATTENDANCE_ALLOWANCE"]
        sal.loc[negA, "REVISED_BASIC"] -= df_[negA]
        sal.loc[negA, "REVISED_ATTENDANCE_ALLOWANCE"] = 0.0
    negO = sal["REVISED_OTHER_DEDUCTION"] < -1
    if negO.any():
        df_ = -sal["REVISED_OTHER_DEDUCTION"]
        sal.loc[negO, "REVISED_OTHER_DEDUCTION"] = 0.0
        sal.loc[negO, "REVISED_ATTENDANCE_ALLOWANCE"] += df_[negO]
        sal.loc[negO, "REVISED_GROSS"] += df_[negO]
        sal.loc[negO, "REVISED_TOTAL_DED"] += df_[negO]

    # ---- C3 final fix: BASIC so 12% x (B+D) = PF exactly (ATT absorbs) -- #
    pfpos = sal["REVISED_PF"] > 0
    tb = np.round(sal["REVISED_PF"] / 0.12)
    cur = sal["REVISED_BASIC"] + sal["REVISED_DA"]
    d = (tb - cur).where(pfpos & ((tb - cur).abs() > 0.5), 0.0)
    sal["REVISED_BASIC"] += d
    sal["REVISED_ATTENDANCE_ALLOWANCE"] -= d

    # ---- M6: ECR_PF>0 => BD month-projection <= 15000 (raise days) ----- #
    bd3 = (sal["REVISED_BASIC"] + sal["REVISED_DA"]).values
    m6 = (sal["ECR_PF"].values > 0) & (bd3 > 0)
    tgt = np.minimum(fmd, np.ceil(bd3 * fmd / 15000))
    sal.loc[m6, "ADJ_WORKING_DAYS"] = np.maximum(sal.loc[m6, "ADJ_WORKING_DAYS"].values,
                                                 tgt[m6]).astype(int)

    sal["REVISED_NET_PAYABLE"] = sal["REVISED_GROSS"] - sal["REVISED_TOTAL_DED"]

    # ---- audit columns ------------------------------------------------- #
    bdf = sal["REVISED_BASIC"] + sal["REVISED_DA"]
    sal["Future_ESI"] = sal["FUTURE_ESI"]
    sal["ESIC AS PER FUTURE"] = np.where(emp_in_esi, sal["FUTURE_ESI"], 0.0)
    sal["ESI DIFFERENCE (Future-REVISED)"] = sal["ESIC AS PER FUTURE"] - sal["REVISED_ESIC"]
    sal["NET_PAYABLE_DIFF"] = sal["REVISED_NET_PAYABLE"] - sal["NET_v"]
    sal["12% OF (REVISED_BASIC+DA)"] = (0.12 * bdf).round(2)
    sal["DIFF (12%_PF vs REVISED_PF)"] = (sal["12% OF (REVISED_BASIC+DA)"] - sal["REVISED_PF"]).round(2)
    sal["REVISED_%"] = np.where(bdf == 0, 0, sal["REVISED_PF"] / bdf.replace(0, np.nan) * 100).round(3)
    sal["0.75% OF REVISED_GROSS"] = (0.0075 * sal["REVISED_GROSS"]).round(2)
    sal["ESI DIFF (0.75% vs REVISED_ESIC)"] = (sal["0.75% OF REVISED_GROSS"] - sal["REVISED_ESIC"]).round(2)
    sal["ESI_%"] = np.where(sal["REVISED_GROSS"] == 0, 0,
                            sal["REVISED_ESIC"] / sal["REVISED_GROSS"].replace(0, np.nan) * 100).round(4)
    sal["MONTHLY_BD_PROJECTION"] = (bdf * fmd / sal["ADJ_WORKING_DAYS"]).round(0)
    sal["MONTHLY_GROSS_PROJECTION"] = (sal["REVISED_GROSS"] * fmd / sal["ADJ_WORKING_DAYS"]).round(0)
    sal["RULE_APPLIED"] = np.select(
        [~emp_in_pf & ~emp_in_esi, sal["IS_MAIN_PF"], emp_in_pf & ~sal["IS_MAIN_PF"]],
        ["NO_PF_NO_ESI", "PF_ANCHOR", "PF_SECONDARY"], default="ESI_ONLY")
    sal["emp_in_pf"], sal["emp_in_esi"] = emp_in_pf.values, emp_in_esi.values
    return sal


# --------------------------------------------------------------------------- #
def validate(sal, fmd):
    pf = sal["REVISED_PF"] > 0
    proj_bd = (sal["REVISED_BASIC"] + sal["REVISED_DA"]) * fmd / sal["ADJ_WORKING_DAYS"]
    esi_strict = int(((sal["REVISED_ESIC"] > 0)
                      & (sal["ESI DIFF (0.75% vs REVISED_ESIC)"].abs() <= 1)).sum())
    esi_relax = int((sal["RULE_075_RELAXED"]).sum())
    checks = {
        "C1 OTHER_DED>=0": (sal["REVISED_OTHER_DEDUCTION"] >= -0.5).all(),
        "C2 NET=GROSS-TOTAL_DED": ((sal["REVISED_NET_PAYABLE"]
                                    - (sal["REVISED_GROSS"] - sal["REVISED_TOTAL_DED"])).abs() <= 1).all(),
        "C3 PF=12%(B+D)": ((sal["DIFF (12%_PF vs REVISED_PF)"].abs() <= 1) | ~pf).all(),
        "C5 ATT_ALW>=0": (sal["REVISED_ATTENDANCE_ALLOWANCE"] >= -0.5).all(),
        "C6 TOTAL_DED>=0": (sal["REVISED_TOTAL_DED"] >= -0.5).all(),
        "C7 GROSS=B+D+ATT": ((sal["REVISED_GROSS"] - (sal["REVISED_BASIC"] + sal["REVISED_DA"]
                              + sal["REVISED_ATTENDANCE_ALLOWANCE"])).abs() <= 1).all(),
        "C8 NET=NETPAYABLE": (sal["NET_PAYABLE_DIFF"].abs() <= 1).all(),
        "C9 days in [1,FM]": sal["ADJ_WORKING_DAYS"].between(1, fmd).all(),
        "C10 ECR_PF>0 => BDproj<=15000": (~((sal["ECR_PF"] > 0) & (proj_bd > 15000.5))).all(),
        "CAP PF<=1800": (sal["REVISED_PF"] <= 1800.5).all(),
        "CAP ESI>0 => GROSS<=21000": (~((sal["REVISED_ESIC"] > 0) & (sal["REVISED_GROSS"] > 21001))).all(),
    }
    print("\nVALIDATION")
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"  INFO  ESI 0.75% strict on {esi_strict} rows; relaxed (GROSS lifted) on {esi_relax} rows")
    return all(checks.values())


# --------------------------------------------------------------------------- #
AUDIT = ["ADJ_WORKING_DAYS", "REVISED_BASIC", "REVISED_DA", "REVISED_ATTENDANCE_ALLOWANCE",
         "REVISED_GROSS", "ECR_PF", "REVISED_PF", "REVISED_ESIC", "Future_ESI",
         "ESIC AS PER FUTURE", "ESI DIFFERENCE (Future-REVISED)", "REVISED_OTHER_DEDUCTION",
         "REVISED_TOTAL_DED", "REVISED_NET_PAYABLE", "NET_PAYABLE_DIFF", "RULE_APPLIED",
         "RULE_075_RELAXED", "12% OF (REVISED_BASIC+DA)", "DIFF (12%_PF vs REVISED_PF)",
         "REVISED_%", "0.75% OF REVISED_GROSS", "ESI DIFF (0.75% vs REVISED_ESIC)", "ESI_%",
         "MONTHLY_BD_PROJECTION", "MONTHLY_GROSS_PROJECTION"]

DROP_ON_LOAD = set(AUDIT) | {
    "ECR_PF", "EMP CODE", "ROW_COUNT", "IS_MAIN_PF", "IS_PRIMARY_ESI", "ECR_PF_CAPPED",
    "SITECODE_C", "FUTURE_ESI", "FUTURE_SITECODE", "ESIC_AS_PER_FUTURE", "ESIC.1",
    "12% OF REVISED_BASIC", "REVISED_%", "%", "remark", "NOTES", "RULE_APPLIED",
    "ADJ_WORKING_DAYS", "REVISED_TOTAL_DED", "emp_in_pf", "emp_in_esi"}

def write_outputs(sal, original_cols, prefix):
    final = sal.copy()
    keep = [c for c in original_cols if c != "ESIC.1"] + AUDIT
    final = final[[c for c in dict.fromkeys(keep) if c in final.columns]]
    fc = f"{prefix}_Final_Complete.xlsx"
    final.to_excel(fc, index=False)
    print(f"\nwrote {fc}  ({final.shape[0]} rows x {final.shape[1]} cols)")

    rep = f"{prefix}_Reconciliation_Report.xlsx"
    fn = resolve(sal, "FULLNAME", required=False) or "EMPCODE"
    with pd.ExcelWriter(rep, engine="openpyxl") as xl:
        summ = sal.groupby("RULE_APPLIED").agg(
            rows=("EMPCODE", "size"), revised_pf=("REVISED_PF", "sum"),
            ecr_pf=("ECR_PF", "sum"), revised_esic=("REVISED_ESIC", "sum"),
            future_esi=("Future_ESI", "sum")).reset_index()
        summ.to_excel(xl, sheet_name="Summary", index=False)
        sal[[c for c in ["EMPCODE", fn, "IS_MAIN_PF", "ECR_PF", "REVISED_PF", "REVISED_BASIC",
             "REVISED_DA", "12% OF (REVISED_BASIC+DA)", "DIFF (12%_PF vs REVISED_PF)", "REVISED_%"]
             if c in sal.columns]].to_excel(xl, sheet_name="PF_Audit", index=False)
        sal[[c for c in ["EMPCODE", "SITECODE_C", "IS_PRIMARY_ESI", "REVISED_ESIC", "Future_ESI",
             "REVISED_GROSS", "0.75% OF REVISED_GROSS", "ESI_%", "RULE_075_RELAXED"]
             if c in sal.columns]].to_excel(xl, sheet_name="ESI_Audit", index=False)
        sal[[c for c in ["EMPCODE", "REVISED_GROSS", "REVISED_PF", "REVISED_ESIC",
             "REVISED_OTHER_DEDUCTION", "REVISED_TOTAL_DED", "REVISED_NET_PAYABLE", "NET_v",
             "NET_PAYABLE_DIFF", "ADJ_WORKING_DAYS", "MONTHLY_BD_PROJECTION",
             "MONTHLY_GROSS_PROJECTION"] if c in sal.columns]].to_excel(xl, sheet_name="Math_Checks", index=False)
        final.to_excel(xl, sheet_name="Reconciled_Data", index=False)
    print(f"wrote {rep}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salary", required=True)
    ap.add_argument("--ecr", nargs="+", required=True)
    ap.add_argument("--future", required=True)
    ap.add_argument("--month", required=True, help="YYYY-MM")
    ap.add_argument("--salary-header", default="auto")
    ap.add_argument("--out-prefix", required=True)
    a = ap.parse_args()

    y, m = map(int, a.month.split("-"))
    fmd = calendar.monthrange(y, m)[1]
    print(f"Month {a.month}  FULL_MONTH={fmd}")
    print("Loading ECR ...");    ecr = load_ecr(a.ecr)
    print("Loading Future ...");  fut = load_future(a.future)
    print("Loading salary ...")
    hdr = detect_salary_header(a.salary) if str(a.salary_header) == "auto" else int(a.salary_header)
    print(f"  salary header row index = {hdr}")
    sal = pd.read_excel(a.salary, header=hdr)
    pre = [c for c in sal.columns if c in DROP_ON_LOAD]
    if pre:
        print(f"  stripping {len(pre)} prior-run/output columns")
        sal = sal.drop(columns=pre)
    original_cols = list(sal.columns)
    print(f"  salary: {sal.shape[0]} rows x {sal.shape[1]} cols")

    sal = reconcile(sal, ecr, fut, fmd)
    print(f"\n  REVISED_PF total {sal['REVISED_PF'].sum():,.0f} (ECR {sal['ECR_PF'].sum():,.0f}) | "
          f"REVISED_ESIC {sal['REVISED_ESIC'].sum():,.0f} (Future {fut['FUTURE_ESI'].sum():,.0f}) | "
          f"NET {sal['REVISED_NET_PAYABLE'].sum():,.0f} (orig {sal['NET_v'].sum():,.0f})")
    ok = validate(sal, fmd)
    write_outputs(sal, original_cols, a.out_prefix)
    print("\nDONE" + ("" if ok else "  (VALIDATION FAILURES — review before filing)"))
    sys.exit(0 if ok else 2)

if __name__ == "__main__":
    main()
