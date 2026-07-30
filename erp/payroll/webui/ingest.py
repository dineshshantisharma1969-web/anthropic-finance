"""
ingest.py — the one code path that turns a reconciled per-employee CSV into
payroll_rows + action_items + Golden-Rule checks. Used by BOTH the load_period.py
CLI and the web 'Run reconciliation' endpoint, so there is a single source of truth.
"""
import csv
from datetime import date
from psycopg2.extras import execute_values, Json

FIELD = {
    "empcode": "emp_code", "fullname": "full_name",
    "sitecode": "site_code", "sitename": "site_name", "sitestate": "site_state",
    "normaldays": "normal_days", "adj_working_days": "adj_working_days",
    "gross amt": "gross_amt", "revised_gross": "revised_gross",
    "netpayable": "net_payable", "ecr_pf": "ecr_pf", "revised_pf": "revised_pf",
    "revised_esic": "revised_esic", "future_esi": "future_esi",
    "rule_applied": "rule_applied",
    "monthly_gross_projection": "monthly_gross_projection",
    "real_full_month_gross": "real_full_month_gross",
    "overpaid_vs_rate": "overpaid_vs_rate",
    "action_needed": "action_needed", "action_reason": "action_reason",
    "excess_salary": "excess_salary",
}


def num(v):
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def truthy(v):
    return str(v).strip().upper() in ("Y", "YES", "TRUE", "1")


def read_rows(fileobj):
    """Parse a reconciled CSV (path or open text file / iterable of lines)."""
    if isinstance(fileobj, str):
        f = open(fileobj, newline="", encoding="utf-8-sig")
        close = True
    else:
        f = fileobj
        close = False
    try:
        rdr = csv.DictReader(f)
        rdr.fieldnames = [h.strip() for h in (rdr.fieldnames or [])]
        out = []
        for raw in rdr:
            r = {}
            for h, v in raw.items():
                key = FIELD.get((h or "").strip().lower())
                if key:
                    r[key] = v
            if r.get("emp_code"):
                out.append(r)
        return out
    finally:
        if close:
            f.close()


def ingest_period(conn, period, fy, rows, run_by=None, source_files=None, net_anchor=None):
    """Load one reconciled month into the schema (idempotent per period).
    Returns a summary dict. Commits on success."""
    cur = conn.cursor()

    cur.execute(
        """INSERT INTO salary_period (period, fy) VALUES (%s, %s)
           ON CONFLICT (period) DO UPDATE SET fy = EXCLUDED.fy RETURNING id;""",
        (period, fy))
    period_id = cur.fetchone()[0]

    cur.execute(
        """INSERT INTO reconciliation_run (period_id, run_by, source_files, rows_loaded)
           VALUES (%s, %s, %s, %s) RETURNING id;""",
        (period_id, run_by, source_files, len(rows)))
    run_id = cur.fetchone()[0]

    first_seen = date(int(period[:4]), int(period[5:7]), 1)
    emps = {}
    for r in rows:
        emps.setdefault(r["emp_code"], r.get("full_name") or r["emp_code"])
    execute_values(cur,
        """INSERT INTO employee (emp_code, full_name, first_seen) VALUES %s
           ON CONFLICT (emp_code) DO UPDATE
             SET full_name = EXCLUDED.full_name,
                 first_seen = LEAST(employee.first_seen, EXCLUDED.first_seen);""",
        [(c, n, first_seen) for c, n in emps.items()])

    sites = {}
    for r in rows:
        if r.get("site_code"):
            sites.setdefault(r["site_code"], (r.get("site_name") or r["site_code"], r.get("site_state")))
    execute_values(cur,
        """INSERT INTO site (site_code, site_name, site_state) VALUES %s
           ON CONFLICT (site_code) DO UPDATE
             SET site_name = EXCLUDED.site_name, site_state = EXCLUDED.site_state;""",
        [(c, nm, st) for c, (nm, st) in sites.items()])

    cur.execute("DELETE FROM payroll_row WHERE period_id = %s;", (period_id,))
    cols = ["period_id", "run_id", "emp_code", "site_code", "normal_days", "adj_working_days",
            "gross_amt", "revised_gross", "net_payable", "ecr_pf", "revised_pf", "revised_esic",
            "future_esi", "rule_applied", "monthly_gross_projection", "real_full_month_gross",
            "overpaid_vs_rate", "action_needed", "action_reason", "excess_salary"]
    values = [(
        period_id, run_id, r["emp_code"], r.get("site_code"),
        num(r.get("normal_days")), num(r.get("adj_working_days")), num(r.get("gross_amt")),
        num(r.get("revised_gross")), num(r.get("net_payable")), num(r.get("ecr_pf")),
        num(r.get("revised_pf")), num(r.get("revised_esic")), num(r.get("future_esi")),
        r.get("rule_applied"), num(r.get("monthly_gross_projection")),
        num(r.get("real_full_month_gross")), num(r.get("overpaid_vs_rate")),
        truthy(r.get("action_needed")), r.get("action_reason"), num(r.get("excess_salary"))
    ) for r in rows]
    execute_values(cur, f"INSERT INTO payroll_row ({','.join(cols)}) VALUES %s", values)

    cur.execute(
        """INSERT INTO action_item (payroll_row_id, period_id, emp_code, site_code, reason, excess_salary)
           SELECT id, period_id, emp_code, site_code, action_reason, excess_salary
           FROM payroll_row WHERE period_id = %s AND action_needed;""", (period_id,))
    n_actions = cur.rowcount

    cur.execute(
        """SELECT round(sum(revised_pf)), round(sum(ecr_pf)), round(sum(net_payable)),
                  round(sum(future_esi)), round(sum(revised_esic))
           FROM payroll_row WHERE period_id = %s;""", (period_id,))
    sum_pf, sum_ecr, sum_net, sum_future_esi, sum_esic = cur.fetchone()
    sum_pf = sum_pf or 0; sum_ecr = sum_ecr or 0; sum_net = sum_net or 0
    net_anchor_v = net_anchor if net_anchor is not None else float(sum_net)
    pf_gap = float(sum_pf) - float(sum_ecr)
    net_drift = float(sum_net) - net_anchor_v
    checks = {"rule1_pf_gap": pf_gap, "rule1_pass": abs(pf_gap) <= 1,
              "rule3_net_drift": net_drift, "rule3_pass": abs(net_drift) <= 1,
              "esi_future_gap": float((sum_future_esi or 0) - (sum_esic or 0)),
              "action_rows": n_actions}

    cur.execute(
        """UPDATE reconciliation_run SET sum_revised_pf=%s, sum_ecr_pf=%s, pf_gap=%s,
               sum_net_payable=%s, net_drift=%s, checks=%s WHERE id=%s;""",
        (sum_pf, sum_ecr, pf_gap, sum_net, net_drift, Json(checks), run_id))
    cur.execute(
        """UPDATE salary_period SET ecr_pf_anchor=%s, net_payable_anchor=%s, future_esi_anchor=%s,
               status = CASE WHEN status='draft' THEN 'reconciled' ELSE status END WHERE id=%s;""",
        (sum_ecr, net_anchor_v, sum_future_esi, period_id))

    conn.commit()
    cur.close()
    return {"period": period, "run_id": run_id, "rows": len(values),
            "employees": len(emps), "sites": len(sites), "action_items": n_actions,
            "sum_revised_pf": float(sum_pf), "sum_ecr_pf": float(sum_ecr),
            "pf_gap": pf_gap, "sum_net_payable": float(sum_net), "net_drift": net_drift,
            "checks": checks}
