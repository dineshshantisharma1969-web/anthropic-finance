#!/usr/bin/env python3
"""
Independently re-verify an already-reconciled <Mon>_Final_Complete.xlsx and append
the "excess salary" action columns (skill: pf-salary-reconciliation, Rule M7).

Re-applies EVERY skill formula from the file alone (no raw ECR/Future needed):
  PF = 12%(B+D), ESI = 0.75%xGROSS, NET unchanged, GROSS/NET identities,
  anchors PF=ECR / ESI=Future, day range, non-negativity.

Then adds, after the existing audit block:
  REAL_FULL_MONTH_GROSS  = FIXEDGROSS x FULL_MONTH / SITEDIVISIONDAYS  (legit full-month pay)
  OVERPAID_VS_RATE       = max(0, REVISED_GROSS - FIXEDGROSS x NORMALDAYS / SITEDIVISIONDAYS)
  ACTION_NEEDED          = Y / N
  ACTION_REASON          = why the row is flagged
  EXCESS_SALARY          = max(0, MONTHLY_GROSS_PROJECTION - REAL_FULL_MONTH_GROSS)   << LAST column

    python verify_excess.py INPUT.xlsx --month 2026-04 --out-prefix April26
"""
from __future__ import annotations
import argparse, calendar, sys
import numpy as np
import pandas as pd

TOL = 1000.0  # rupee threshold above which an implied excess is worth flagging


def _norm(s):
    return "".join(str(s).strip().upper().split())

def resolve(df, *names, required=True):
    lut = {_norm(c): c for c in df.columns}
    for n in names:
        if _norm(n) in lut:
            return lut[_norm(n)]
    if required:
        raise KeyError(f"None of {names} found. sample={list(df.columns)[:30]}")
    return None

def num(df, *names, required=True):
    c = resolve(df, *names, required=required)
    if c is None:
        return pd.Series(0.0, index=df.index)
    return pd.to_numeric(df[c], errors="coerce").fillna(0.0).astype(float)


def verify(df):
    """Re-derive every invariant from the file; return (all_ok, list-of-(name,ok,detail))."""
    rpf   = num(df, "REVISED_PF")
    ecrpf = num(df, "ECR_PF")
    resi  = num(df, "REVISED_ESIC")
    fut_q = num(df, "ESIC AS PER FUTURE")
    rb    = num(df, "REVISED_BASIC")
    rda   = num(df, "REVISED_DA")
    ratt  = num(df, "REVISED_ATTENDANCE_ALLOWANCE")
    rg    = num(df, "REVISED_GROSS")
    rod   = num(df, "REVISED_OTHER_DEDUCTION")
    rtd   = num(df, "REVISED_TOTAL_DED")
    rnet  = num(df, "REVISED_NET_PAYABLE")
    onet  = num(df, "NETPAYABLE", "NET PAYABLE")
    adj   = num(df, "ADJ_WORKING_DAYS")
    relax = df[resolve(df, "RULE_075_RELAXED")].astype(bool) if resolve(df, "RULE_075_RELAXED", required=False) else pd.Series(False, index=df.index)
    bd = rb + rda
    rows = []

    def chk(name, mask_bad, fmt=None):
        bad = int(mask_bad.sum())
        ex = ""
        if bad:
            idx = df.index[mask_bad][:5]
            ex = "  e.g. rows " + ",".join(map(str, idx.tolist()))
        rows.append((name, bad == 0, f"{bad} offending{ex}"))

    chk("PF anchor  |REVISED_PF - ECR_PF| <= 1",            (rpf - ecrpf).abs() > 1)
    chk("ESI anchor |REVISED_ESIC - 'ESIC AS PER FUTURE'| <= 1", (resi - fut_q).abs() > 1)
    chk("C3 PF = 12% x (REVISED_BASIC+DA)  [on PF>0]",      ((rpf - 0.12 * bd).abs() > 1) & (rpf > 0))
    chk("ESI = 0.75% x GROSS  [non-relaxed]",               ((resi - 0.0075 * rg).abs() > 1) & (resi > 0) & (~relax))
    chk("C7 GROSS = BASIC+DA+ATT",                          (rg - (bd + ratt)).abs() > 1)
    chk("C2 NET = GROSS - TOTAL_DED",                       (rnet - (rg - rtd)).abs() > 1)
    chk("C8 NET unchanged  |REVISED_NET - NETPAYABLE| <= 1", (rnet - onet).abs() > 1)
    chk("C1 OTHER_DED >= 0",                                rod < -0.5)
    chk("C5 ATT_ALW >= 0",                                  ratt < -0.5)
    chk("C6 TOTAL_DED >= 0",                                rtd < -0.5)
    chk("C9 ADJ_WORKING_DAYS in [1,31]",                    ~adj.between(1, 31))

    ok = all(r[1] for r in rows)
    # totals (informational)
    tot = {
        "REVISED_PF": rpf.sum(), "ECR_PF": ecrpf.sum(),
        "REVISED_ESIC": resi.sum(), "ESIC AS PER FUTURE": fut_q.sum(),
        "REVISED_NET": rnet.sum(), "NETPAYABLE(orig)": onet.sum(),
    }
    return ok, rows, tot


def add_excess(df, fmd):
    fg  = num(df, "FIXEDGROSS", "FIXED_GROSS")
    sdd = num(df, "SITEDIVISIONDAYS")
    nd  = num(df, "NORMALDAYS")
    rg  = num(df, "REVISED_GROSS")
    mgp = num(df, "MONTHLY_GROSS_PROJECTION")
    anom = df[resolve(df, "ANOMALY_BELOW_CEILING")].astype(bool) if resolve(df, "ANOMALY_BELOW_CEILING", required=False) else pd.Series(False, index=df.index)

    has_rate = fg > 0
    sdd_ = np.where(sdd > 0, sdd, float(fmd))
    real_fm = np.where(has_rate, np.round(fg * fmd / sdd_), np.nan)          # legit full-month pay
    rate_days = np.where(has_rate, fg * nd / sdd_, np.nan)                   # legit pay for days worked
    overpaid = np.where(has_rate, np.maximum(0.0, np.round(rg - rate_days)), np.nan)
    excess = np.where(has_rate, np.maximum(0.0, np.round(mgp - real_fm)), np.nan)  # headline

    flagged = has_rate & (excess > TOL)
    low_days = (nd <= 3).values                      # few days => projection blown up by x(FM/days)
    reason = np.full(len(df), "", dtype=object)
    reason[~has_rate] = "NO_FIXED_RATE (cannot assess)"
    reason[flagged & low_days] = ("LOW ATTENDANCE DAYS - verify attendance "
                                  "(few days vs gross => projection inflated)")
    sel = flagged & ~low_days & anom.values
    reason[sel] = "ESI-EXEMPT but real full-month rate <= Rs.21,000 - should be in ESI"
    sel = flagged & ~low_days & ~anom.values & (np.nan_to_num(overpaid) > TOL)
    reason[sel] = "PAID ABOVE FIXED RATE this month"
    sel = flagged & (reason == "")
    reason[sel] = "IMPLIED FULL-MONTH >> fixed rate - review"

    add = pd.DataFrame({
        "REAL_FULL_MONTH_GROSS": real_fm,
        "OVERPAID_VS_RATE": overpaid,
        "ACTION_NEEDED": np.where(flagged, "Y", "N"),
        "ACTION_REASON": reason,
        "EXCESS_SALARY": excess,           # appended LAST
    }, index=df.index)
    df = pd.concat([df, add], axis=1)
    return df, int(flagged.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("--month", required=True, help="YYYY-MM")
    ap.add_argument("--out-prefix", required=True)
    ap.add_argument("--outdir", default=".")
    a = ap.parse_args()
    y, m = map(int, a.month.split("-"))
    fmd = calendar.monthrange(y, m)[1]

    print(f"Reading {a.infile}")
    df = pd.read_excel(a.infile)
    print(f"  {df.shape[0]} rows x {df.shape[1]} cols   FULL_MONTH={fmd}")

    print("\n=== VERIFICATION (re-derived from the file) ===")
    ok, rows, tot = verify(df)
    for name, good, detail in rows:
        print(f"  {'PASS' if good else 'FAIL'}  {name:48} {('' if good else detail)}")
    print("  --- totals ---")
    print(f"    REVISED_PF {tot['REVISED_PF']:,.0f}  vs ECR_PF {tot['ECR_PF']:,.0f}")
    print(f"    REVISED_ESIC {tot['REVISED_ESIC']:,.0f}  vs ESIC-as-per-Future {tot['ESIC AS PER FUTURE']:,.0f}")
    print(f"    REVISED_NET {tot['REVISED_NET']:,.0f}  vs NETPAYABLE(orig) {tot['NETPAYABLE(orig)']:,.0f}")
    print(f"  OVERALL: {'ALL CHECKS PASS' if ok else 'FAILURES PRESENT - review above'}")

    print("\n=== EXCESS SALARY (Rule M7 action column) ===")
    df, nflag = add_excess(df, fmd)
    es = pd.to_numeric(df["EXCESS_SALARY"], errors="coerce")
    print(f"  ACTION_NEEDED=Y on {nflag} rows  (EXCESS_SALARY > Rs.{TOL:,.0f})")
    print(f"  EXCESS_SALARY  median={es.median():,.0f}  p95={es.quantile(.95):,.0f}  max={es.max():,.0f}")
    print("  ACTION_REASON breakdown:")
    for r, c in df.loc[df["ACTION_NEEDED"] == "Y", "ACTION_REASON"].value_counts().items():
        print(f"    {c:>6}  {r}")

    # ---- outputs ----
    full = f"{a.outdir}/{a.out_prefix}_Final_Complete_with_Excess.xlsx"
    df.to_excel(full, index=False)
    print(f"\nwrote {full}  ({df.shape[0]} x {df.shape[1]})")

    EMP = resolve(df, "EMPCODE", "EMP CODE"); FN = resolve(df, "FULLNAME", required=False)
    slim = [c for c in [EMP, FN, "SITECODE", "DESIGNATIONNAME", "NORMALDAYS",
            "ADJ_WORKING_DAYS", "REVISED_GROSS", "FIXEDGROSS", "SITEDIVISIONDAYS",
            "REAL_FULL_MONTH_GROSS", "MONTHLY_GROSS_PROJECTION", "OVERPAID_VS_RATE",
            "REVISED_PF", "REVISED_ESIC", "ANOMALY_BELOW_CEILING", "ACTION_REASON",
            "EXCESS_SALARY"] if c in df.columns]
    act = df[df["ACTION_NEEDED"] == "Y"][slim].sort_values("EXCESS_SALARY", ascending=False)
    rep = pd.DataFrame([(n, "PASS" if g else "FAIL", d) for n, g, d in rows],
                       columns=["Check", "Result", "Detail"])
    al = f"{a.outdir}/{a.out_prefix}_Action_List.xlsx"
    with pd.ExcelWriter(al, engine="openpyxl") as xl:
        rep.to_excel(xl, sheet_name="Verification_Report", index=False)
        act.to_excel(xl, sheet_name="Action_List", index=False)
    print(f"wrote {al}  (Action_List rows: {len(act)})")
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
