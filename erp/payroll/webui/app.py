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
                   rule_mix=rule_mix, status_mix=status_mix, run=run,
                   golden=live_golden(period))


def live_golden(period):
    """Golden Rules recomputed from CURRENT figures vs the frozen anchors, so an
    edit that breaks an invariant flips the badge to REVIEW immediately."""
    p = q("""SELECT id, status, net_payable_anchor, ecr_pf_anchor, future_esi_anchor
             FROM salary_period WHERE period = %s""", (period,), one=True)
    if not p:
        return None
    s = q("""SELECT coalesce(sum(revised_pf),0) rp, coalesce(sum(ecr_pf),0) ep,
                    coalesce(sum(net_payable),0) np, coalesce(sum(revised_esic),0) re
             FROM payroll_row WHERE period_id = %s""", (p["id"],), one=True)
    pf_gap  = float(s["rp"]) - float(s["ep"])
    net_drift = float(s["np"]) - float(p["net_payable_anchor"] or s["np"])
    esi_gap = float(p["future_esi_anchor"] or 0) - float(s["re"])
    return {"status": p["status"], "pf_gap": pf_gap,
            "net_drift": net_drift, "esi_gap": esi_gap}


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
        SELECT a.id, r.id AS payroll_row_id, a.emp_code, e.full_name, a.site_code,
               s.site_name, s.site_state,
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


# Financial figures a correction may touch. Everything else is off-limits to
# hand edits (identity, rule, projections) — those come from a re-load.
EDITABLE_FIGURES = {"gross_amt", "revised_gross", "net_payable",
                    "ecr_pf", "revised_pf", "revised_esic",
                    "adj_working_days", "excess_salary"}
LOCKED_STATES = {"filed", "closed"}


@app.patch("/api/payroll/<int:rid>")
def edit_figure(rid):
    """Correct one financial figure on one payroll row — audited, and only while
    the period is unlocked. Requires field, value, reason (and who)."""
    body = request.get_json(force=True) or {}
    field = body.get("field")
    reason = (body.get("reason") or "").strip()
    changed_by = body.get("changed_by") or "unknown"
    if field not in EDITABLE_FIGURES:
        return jsonify(error=f"field '{field}' is not editable by hand"), 400
    if not reason:
        return jsonify(error="a reason is required for a financial edit"), 400

    row = q("""SELECT r.*, p.period, p.status
               FROM payroll_row r JOIN salary_period p ON p.id = r.period_id
               WHERE r.id = %s""", (rid,), one=True)
    if not row:
        return jsonify(error="row not found"), 404
    if row["status"] in LOCKED_STATES:
        return jsonify(error=f"period {row['period']} is {row['status']} — locked. "
                             "Reopen it (with a reason) or post an adjustment in a later month."), 423

    try:
        new_val = None if body.get("value") in (None, "") else float(body["value"])
    except (TypeError, ValueError):
        return jsonify(error="value must be numeric"), 400
    old_val = row[field]

    q(f"UPDATE payroll_row SET {field} = %s WHERE id = %s", (new_val, rid))
    q("""INSERT INTO figure_change (entity, entity_id, period_id, emp_code, field,
                                    old_value, new_value, changed_by, reason)
         VALUES ('payroll_row', %s, %s, %s, %s, %s, %s, %s, %s)""",
      (rid, row["period_id"], row["emp_code"], field,
       None if old_val is None else str(old_val),
       None if new_val is None else str(new_val), changed_by, reason))
    # keep the action_item excess in sync when that is the edited figure
    if field == "excess_salary":
        q("UPDATE action_item SET excess_salary = %s WHERE payroll_row_id = %s", (new_val, rid))

    return jsonify(id=rid, field=field, old=old_val, new=new_val,
                   golden=live_golden(row["period"]))


@app.post("/api/periods/<period>/status")
def set_status(period):
    """Move a period through draft → reconciled → filed → closed, or reopen a
    filed/closed period (which requires a reason). All transitions are audited."""
    body = request.get_json(force=True) or {}
    new = body.get("status")
    reason = (body.get("reason") or "").strip()
    changed_by = body.get("changed_by") or "unknown"
    if new not in ("draft", "reconciled", "filed", "closed"):
        return jsonify(error="bad status"), 400
    p = q("SELECT id, status FROM salary_period WHERE period = %s", (period,), one=True)
    if not p:
        return jsonify(error="period not found"), 404
    # reopening a locked period is privileged: demand a reason
    if p["status"] in LOCKED_STATES and new not in LOCKED_STATES and not reason:
        return jsonify(error=f"reopening a {p['status']} period requires a reason"), 400

    q("UPDATE salary_period SET status = %s WHERE id = %s", (new, p["id"]))
    q("""INSERT INTO figure_change (entity, entity_id, period_id, field,
                                    old_value, new_value, changed_by, reason)
         VALUES ('salary_period', %s, %s, 'status', %s, %s, %s, %s)""",
      (p["id"], p["id"], p["status"], new, changed_by,
       reason or f"status {p['status']} → {new}"))
    return jsonify(period=period, status=new)


@app.get("/api/audit")
def audit():
    """Recent changes for a period (figure edits + status transitions)."""
    period = request.args.get("period")
    limit = min(int(request.args.get("limit", 50)), 500)
    rows = q("""SELECT fc.changed_at, fc.entity, fc.emp_code, fc.field,
                       fc.old_value, fc.new_value, fc.changed_by, fc.reason,
                       e.full_name
                FROM figure_change fc
                JOIN salary_period p ON p.id = fc.period_id
                LEFT JOIN employee e ON e.emp_code = fc.emp_code
                WHERE p.period = %s
                ORDER BY fc.changed_at DESC LIMIT %s""", (period, limit))
    return jsonify(rows=rows)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port, debug=False)
