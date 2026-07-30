#!/usr/bin/env python3
"""
app.py — ISPL ERP Payroll web UI (Flask + Postgres).

A DB-backed console for the payroll module: browse periods, see the Golden-Rule
position at a glance, and — the point of it — work the ACTION_NEEDED list as
tickets whose status changes are persisted back to the database.

Run:
  pip install -r requirements.txt
  export ERP_DB="host=<h> port=5432 user=<u> password=<p> dbname=postgres"
  python app.py                       # serves http://127.0.0.1:8000

For local validation against a unix-socket Postgres:
  export ERP_DB="host=/tmp/pgs user=postgres dbname=erp"
  python app.py
"""
import os
from flask import Flask, jsonify, request, send_from_directory
import psycopg2
from psycopg2.extras import RealDictCursor

DSN = os.environ.get("ERP_DB", "host=/tmp/pgs user=postgres dbname=erp")
HERE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(HERE, "static"), static_url_path="")


def q(sql, args=None, one=False):
    conn = psycopg2.connect(DSN)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, args or ())
            if cur.description is None:
                conn.commit()
                return cur.rowcount
            rows = cur.fetchall()
            conn.commit()
            return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/health")
def health():
    try:
        q("SELECT 1", one=True)
        return jsonify(ok=True)
    except Exception as e:  # noqa: BLE001
        return jsonify(ok=False, error=str(e)), 500


@app.get("/api/periods")
def periods():
    return jsonify(q("SELECT * FROM v_period_summary ORDER BY period DESC"))


@app.get("/api/summary")
def summary():
    """KPIs + reason breakdown + rule mix + latest-run Golden-Rule checks."""
    period = request.args.get("period")
    if not period:
        row = q("SELECT period FROM salary_period ORDER BY period DESC LIMIT 1", one=True)
        period = row and row["period"]
    if not period:
        return jsonify(period=None)

    kpis = q("SELECT * FROM v_period_summary WHERE period = %s", (period,), one=True)
    reasons = q(
        """SELECT r.action_reason AS reason,
                  count(*)                    AS items,
                  round(sum(r.excess_salary)) AS excess_salary
           FROM payroll_row r JOIN salary_period p ON p.id = r.period_id
           WHERE p.period = %s AND r.action_needed
           GROUP BY r.action_reason ORDER BY excess_salary DESC NULLS LAST""",
        (period,))
    rule_mix = q(
        """SELECT r.rule_applied AS rule, count(*) AS rows
           FROM payroll_row r JOIN salary_period p ON p.id = r.period_id
           WHERE p.period = %s GROUP BY r.rule_applied ORDER BY rows DESC""",
        (period,))
    status_mix = q(
        """SELECT a.status, count(*) AS items
           FROM action_item a JOIN salary_period p ON p.id = a.period_id
           WHERE p.period = %s GROUP BY a.status""",
        (period,))
    run = q(
        """SELECT run_at, run_by, source_files, rows_loaded, pf_gap, net_drift, checks
           FROM reconciliation_run rr JOIN salary_period p ON p.id = rr.period_id
           WHERE p.period = %s ORDER BY run_at DESC LIMIT 1""",
        (period,), one=True)
    return jsonify(period=period, kpis=kpis, reasons=reasons,
                   rule_mix=rule_mix, status_mix=status_mix, run=run)


@app.get("/api/actions")
def actions():
    """Paginated action tickets for a period, with filters."""
    period = request.args.get("period")
    status = request.args.get("status")
    reason = request.args.get("reason")
    search = request.args.get("q")
    limit = min(int(request.args.get("limit", 50)), 500)
    offset = int(request.args.get("offset", 0))

    where = ["p.period = %s"]
    args = [period]
    if status and status != "all":
        where.append("a.status = %s"); args.append(status)
    if reason and reason != "all":
        where.append("a.reason = %s"); args.append(reason)
    if search:
        where.append("(a.emp_code ILIKE %s OR e.full_name ILIKE %s OR s.site_name ILIKE %s)")
        args += [f"%{search}%", f"%{search}%", f"%{search}%"]
    w = " AND ".join(where)

    total = q(f"""SELECT count(*) AS n FROM action_item a
                  JOIN salary_period p ON p.id = a.period_id
                  JOIN employee e ON e.emp_code = a.emp_code
                  JOIN site s ON s.site_code = a.site_code
                  WHERE {w}""", args, one=True)["n"]
    rows = q(f"""
        SELECT a.id, a.emp_code, e.full_name, a.site_code, s.site_name, s.site_state,
               a.reason, a.excess_salary, a.status, a.assigned_to, a.resolution_note,
               r.gross_amt, r.net_payable, r.revised_pf, r.rule_applied
        FROM action_item a
        JOIN salary_period p ON p.id = a.period_id
        JOIN employee e ON e.emp_code = a.emp_code
        JOIN site s ON s.site_code = a.site_code
        JOIN payroll_row r ON r.id = a.payroll_row_id
        WHERE {w}
        ORDER BY a.excess_salary DESC NULLS LAST
        LIMIT %s OFFSET %s""", args + [limit, offset])
    return jsonify(total=total, limit=limit, offset=offset, rows=rows)


@app.patch("/api/actions/<int:aid>")
def update_action(aid):
    body = request.get_json(force=True) or {}
    fields, args = [], []
    if "status" in body:
        if body["status"] not in ("open", "investigating", "resolved", "waived"):
            return jsonify(error="bad status"), 400
        fields.append("status = %s"); args.append(body["status"])
    if "assigned_to" in body:
        fields.append("assigned_to = %s"); args.append(body["assigned_to"] or None)
    if "resolution_note" in body:
        fields.append("resolution_note = %s"); args.append(body["resolution_note"] or None)
    if not fields:
        return jsonify(error="nothing to update"), 400
    fields.append("updated_at = now()")
    args.append(aid)
    q(f"UPDATE action_item SET {', '.join(fields)} WHERE id = %s", args)
    return jsonify(q("SELECT id, status, assigned_to, resolution_note FROM action_item WHERE id = %s",
                     (aid,), one=True))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port, debug=False)
