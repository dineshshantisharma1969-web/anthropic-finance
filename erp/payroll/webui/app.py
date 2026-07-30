#!/usr/bin/env python3
"""
app.py — ISPL ERP Payroll web UI (Flask + Postgres) with auth + roles.

A DB-backed console for the payroll module: browse periods, see the Golden-Rule
position, and work the ACTION_NEEDED list as tickets. Financial figures are
correctable while a period is open and locked once filed — every change audited
against the logged-in user.

Roles (each inherits the ones above):
  viewer   → read-only
  clerk    → + work tickets, correct figures on open periods
  approver → + file/close periods, reopen locked periods
  admin    → + manage users (via manage_users.py)

Run:
  pip install -r requirements.txt
  export ERP_DB="host=<h> port=5432 user=<u> password=<p> dbname=postgres"
  export ERP_SECRET="<a long random string>"      # REQUIRED in production
  python manage_users.py add dinesh --role admin   # seed a first user
  python app.py                                    # http://127.0.0.1:8000
"""
import os
from functools import wraps
from flask import Flask, jsonify, request, session, send_from_directory
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import ingest

DSN = os.environ.get("ERP_DB", "host=/tmp/pgs user=postgres dbname=erp")
HERE = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.environ.get("ERP_UPLOAD_DIR", os.path.join(HERE, "uploads"))
INPUT_TYPES = ("salary", "pf", "esi")
INPUT_LABELS = {"salary": "Salary sheet", "pf": "ECR / PF", "esi": "ESI / Future"}


def fy_of(period):
    """Indian FY (Apr–Mar) label for a YYYY-MM period, e.g. 2026-06 → '2026-27'."""
    y, m = int(period[:4]), int(period[5:7])
    start = y if m >= 4 else y - 1
    return f"{start}-{str(start + 1)[-2:]}"
app = Flask(__name__, static_folder=os.path.join(HERE, "static"), static_url_path="")
app.secret_key = os.environ.get("ERP_SECRET", "dev-insecure-secret-change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

# role → the set of roles it satisfies (admin satisfies everything)
RANK = {"viewer": 0, "clerk": 1, "approver": 2, "admin": 3}


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


# ---------------------------------------------------------------- auth plumbing
def current_user():
    return session.get("user")


def login_required(fn):
    @wraps(fn)
    def w(*a, **k):
        if not current_user():
            return jsonify(error="login required"), 401
        return fn(*a, **k)
    return w


def require_role(minimum):
    """Gate an endpoint: the user's role rank must be >= `minimum`."""
    def deco(fn):
        @wraps(fn)
        def w(*a, **k):
            u = current_user()
            if not u:
                return jsonify(error="login required"), 401
            if RANK.get(u["role"], -1) < RANK[minimum]:
                return jsonify(error=f"requires {minimum} role or higher"), 403
            return fn(*a, **k)
        return w
    return deco


def actor():
    """The audit 'changed_by' — always the authenticated user, never client text."""
    u = current_user() or {}
    return u.get("full_name") or u.get("username") or "unknown"


@app.post("/api/login")
def login():
    body = request.get_json(force=True) or {}
    u = q("SELECT username, password_hash, full_name, role, active FROM app_user WHERE username = %s",
          (body.get("username", "").strip(),), one=True)
    if not u or not u["active"] or not check_password_hash(u["password_hash"], body.get("password", "")):
        return jsonify(error="invalid username or password"), 401
    session["user"] = {"username": u["username"], "full_name": u["full_name"], "role": u["role"]}
    session.permanent = True
    return jsonify(user=session["user"])


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/me")
def me():
    u = current_user()
    return (jsonify(user=u) if u else (jsonify(error="not logged in"), 401))


# ---------------------------------------------------------------- static
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


# ---------------------------------------------------------------- read (any user)
@app.get("/api/periods")
@login_required
def periods():
    return jsonify(q("SELECT * FROM v_period_summary ORDER BY period DESC"))


@app.get("/api/summary")
@login_required
def summary():
    period = request.args.get("period")
    if not period:
        row = q("SELECT period FROM salary_period ORDER BY period DESC LIMIT 1", one=True)
        period = row and row["period"]
    if not period:
        return jsonify(period=None)

    kpis = q("SELECT * FROM v_period_summary WHERE period = %s", (period,), one=True)
    reasons = q(
        """SELECT r.action_reason AS reason, count(*) AS items,
                  round(sum(r.excess_salary)) AS excess_salary
           FROM payroll_row r JOIN salary_period p ON p.id = r.period_id
           WHERE p.period = %s AND r.action_needed
           GROUP BY r.action_reason ORDER BY excess_salary DESC NULLS LAST""", (period,))
    rule_mix = q(
        """SELECT r.rule_applied AS rule, count(*) AS rows
           FROM payroll_row r JOIN salary_period p ON p.id = r.period_id
           WHERE p.period = %s GROUP BY r.rule_applied ORDER BY rows DESC""", (period,))
    status_mix = q(
        """SELECT a.status, count(*) AS items
           FROM action_item a JOIN salary_period p ON p.id = a.period_id
           WHERE p.period = %s GROUP BY a.status""", (period,))
    run = q(
        """SELECT run_at, run_by, source_files, rows_loaded, pf_gap, net_drift, checks
           FROM reconciliation_run rr JOIN salary_period p ON p.id = rr.period_id
           WHERE p.period = %s ORDER BY run_at DESC LIMIT 1""", (period,), one=True)
    return jsonify(period=period, kpis=kpis, reasons=reasons, rule_mix=rule_mix,
                   status_mix=status_mix, run=run, golden=live_golden(period))


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
    return {"status": p["status"],
            "pf_gap": float(s["rp"]) - float(s["ep"]),
            "net_drift": float(s["np"]) - float(p["net_payable_anchor"] or s["np"]),
            "esi_gap": float(p["future_esi_anchor"] or 0) - float(s["re"])}


@app.get("/api/actions")
@login_required
def actions():
    period = request.args.get("period")
    status = request.args.get("status")
    reason = request.args.get("reason")
    search = request.args.get("q")
    limit = min(int(request.args.get("limit", 50)), 500)
    offset = int(request.args.get("offset", 0))

    where = ["p.period = %s"]; args = [period]
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
                  JOIN site s ON s.site_code = a.site_code WHERE {w}""", args, one=True)["n"]
    rows = q(f"""
        SELECT a.id, r.id AS payroll_row_id, a.emp_code, e.full_name, a.site_code,
               s.site_name, s.site_state, a.reason, a.excess_salary, a.status,
               a.assigned_to, a.resolution_note,
               r.gross_amt, r.net_payable, r.revised_pf, r.rule_applied
        FROM action_item a
        JOIN salary_period p ON p.id = a.period_id
        JOIN employee e ON e.emp_code = a.emp_code
        JOIN site s ON s.site_code = a.site_code
        JOIN payroll_row r ON r.id = a.payroll_row_id
        WHERE {w} ORDER BY a.excess_salary DESC NULLS LAST
        LIMIT %s OFFSET %s""", args + [limit, offset])
    return jsonify(total=total, limit=limit, offset=offset, rows=rows)


# ---------------------------------------------------------------- write (gated)
@app.patch("/api/actions/<int:aid>")
@require_role("clerk")
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
    fields.append("updated_at = now()"); args.append(aid)
    q(f"UPDATE action_item SET {', '.join(fields)} WHERE id = %s", args)
    return jsonify(q("SELECT id, status, assigned_to, resolution_note FROM action_item WHERE id = %s",
                     (aid,), one=True))


EDITABLE_FIGURES = {"gross_amt", "revised_gross", "net_payable", "ecr_pf",
                    "revised_pf", "revised_esic", "adj_working_days", "excess_salary"}
LOCKED_STATES = {"filed", "closed"}


@app.patch("/api/payroll/<int:rid>")
@require_role("clerk")
def edit_figure(rid):
    """Correct one financial figure — audited against the logged-in user, and
    only while the period is unlocked."""
    body = request.get_json(force=True) or {}
    field = body.get("field")
    reason = (body.get("reason") or "").strip()
    if field not in EDITABLE_FIGURES:
        return jsonify(error=f"field '{field}' is not editable by hand"), 400
    if not reason:
        return jsonify(error="a reason is required for a financial edit"), 400

    row = q("""SELECT r.*, p.period, p.status FROM payroll_row r
               JOIN salary_period p ON p.id = r.period_id WHERE r.id = %s""", (rid,), one=True)
    if not row:
        return jsonify(error="row not found"), 404
    if row["status"] in LOCKED_STATES:
        return jsonify(error=f"period {row['period']} is {row['status']} — locked. "
                             "An approver must reopen it (with a reason), or post an "
                             "adjustment in a later month."), 423
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
       None if new_val is None else str(new_val), actor(), reason))
    if field == "excess_salary":
        q("UPDATE action_item SET excess_salary = %s WHERE payroll_row_id = %s", (new_val, rid))
    return jsonify(id=rid, field=field, old=old_val, new=new_val, by=actor(),
                   golden=live_golden(row["period"]))


@app.post("/api/periods/<period>/status")
@require_role("approver")
def set_status(period):
    """File/close a period or reopen a locked one — approver+ only, all audited."""
    body = request.get_json(force=True) or {}
    new = body.get("status")
    reason = (body.get("reason") or "").strip()
    if new not in ("draft", "reconciled", "filed", "closed"):
        return jsonify(error="bad status"), 400
    p = q("SELECT id, status FROM salary_period WHERE period = %s", (period,), one=True)
    if not p:
        return jsonify(error="period not found"), 404
    if p["status"] in LOCKED_STATES and new not in LOCKED_STATES and not reason:
        return jsonify(error=f"reopening a {p['status']} period requires a reason"), 400

    q("UPDATE salary_period SET status = %s WHERE id = %s", (new, p["id"]))
    q("""INSERT INTO figure_change (entity, entity_id, period_id, field,
                                    old_value, new_value, changed_by, reason)
         VALUES ('salary_period', %s, %s, 'status', %s, %s, %s, %s)""",
      (p["id"], p["id"], p["status"], new, actor(),
       reason or f"status {p['status']} → {new}"))
    return jsonify(period=period, status=new)


@app.get("/api/audit")
@login_required
def audit():
    period = request.args.get("period")
    limit = min(int(request.args.get("limit", 50)), 500)
    rows = q("""SELECT fc.changed_at, fc.entity, fc.emp_code, fc.field,
                       fc.old_value, fc.new_value, fc.changed_by, fc.reason, e.full_name
                FROM figure_change fc
                JOIN salary_period p ON p.id = fc.period_id
                LEFT JOIN employee e ON e.emp_code = fc.emp_code
                WHERE p.period = %s ORDER BY fc.changed_at DESC LIMIT %s""", (period, limit))
    return jsonify(rows=rows)


# ---------------------------------------------------------------- intake
def may_upload(username, role, input_type):
    if role == "admin":
        return True
    row = q("SELECT 1 FROM input_owner WHERE input_type=%s AND username=%s",
            (input_type, username), one=True)
    return bool(row)


@app.get("/api/intake")
@login_required
def intake():
    """Readiness board for a period: the three input slots, who owns each, what's
    been uploaded, and whether the period is ready to reconcile."""
    period = request.args.get("period")
    if not period:
        return jsonify(error="period required"), 400
    u = current_user()
    p = q("SELECT id, status FROM salary_period WHERE period=%s", (period,), one=True)
    period_id = p["id"] if p else None
    has_rows = False
    if period_id:
        has_rows = q("SELECT 1 FROM payroll_row WHERE period_id=%s LIMIT 1", (period_id,), one=True) is not None

    owners = {t: [] for t in INPUT_TYPES}
    for r in q("SELECT input_type, username FROM input_owner ORDER BY username"):
        owners[r["input_type"]].append(r["username"])

    slots = []
    for t in INPUT_TYPES:
        latest = None
        if period_id:
            latest = q("""SELECT filename, uploaded_by, uploaded_at, status, byte_size
                          FROM period_input WHERE period_id=%s AND input_type=%s
                          ORDER BY uploaded_at DESC LIMIT 1""", (period_id, t), one=True)
        slots.append({"input_type": t, "label": INPUT_LABELS[t], "owners": owners[t],
                      "received": latest is not None, "latest": latest,
                      "may_upload": may_upload(u["username"], u["role"], t)})
    ready = all(s["received"] for s in slots)
    return jsonify(period=period, fy=fy_of(period), status=(p["status"] if p else None),
                   has_rows=has_rows, ready=ready, slots=slots,
                   can_reconcile=(RANK.get(u["role"], -1) >= RANK["approver"]))


@app.post("/api/intake/<period>/<input_type>")
@require_role("clerk")
def upload_input(period, input_type):
    """A preparer uploads their input file for a period. Owner-locked by type."""
    if input_type not in INPUT_TYPES:
        return jsonify(error="unknown input type"), 400
    u = current_user()
    if not may_upload(u["username"], u["role"], input_type):
        return jsonify(error=f"you are not an owner of the {INPUT_LABELS[input_type]} input"), 403
    if "file" not in request.files or not request.files["file"].filename:
        return jsonify(error="no file"), 400
    f = request.files["file"]

    # get-or-create the period (starts as draft = intake in progress)
    p = q("""INSERT INTO salary_period (period, fy) VALUES (%s, %s)
             ON CONFLICT (period) DO UPDATE SET fy=EXCLUDED.fy RETURNING id, status""",
          (period, fy_of(period)), one=True)
    dest_dir = os.path.join(UPLOAD_DIR, period)
    os.makedirs(dest_dir, exist_ok=True)
    safe = secure_filename(f.filename)
    path = os.path.join(dest_dir, f"{input_type}__{safe}")
    f.save(path)
    size = os.path.getsize(path)
    q("""INSERT INTO period_input (period_id, input_type, filename, byte_size, stored_path, uploaded_by)
         VALUES (%s,%s,%s,%s,%s,%s)""",
      (p["id"], input_type, f.filename, size, path, u["username"]))
    return jsonify(ok=True, period=period, input_type=input_type,
                   filename=f.filename, uploaded_by=u["username"], byte_size=size)


@app.post("/api/reconcile/<period>")
@require_role("approver")
def reconcile(period):
    """Approver loads a month's PROCESSED reconciliation file (the per-employee
    output of the local reconcile.py run) — this is the primary way data enters a
    month. The period is created if it doesn't exist. The raw-input intake board
    is optional and does not gate this."""
    if "file" not in request.files or not request.files["file"].filename:
        return jsonify(error="attach the processed reconciliation file (CSV)"), 400

    import io
    stream = io.TextIOWrapper(request.files["file"].stream, encoding="utf-8-sig")
    rows = ingest.read_rows(stream)
    if not rows:
        return jsonify(error="no data rows in the reconciled CSV"), 400
    conn = psycopg2.connect(DSN)
    try:
        summary = ingest.ingest_period(
            conn, period, fy_of(period), rows,
            run_by=current_user()["full_name"],
            source_files="processed file: " + request.files["file"].filename)
    finally:
        conn.close()
    return jsonify(ok=True, **summary)


if __name__ == "__main__":
    if app.secret_key == "dev-insecure-secret-change-me":
        print("WARNING: ERP_SECRET not set — using an insecure dev key. Set it in production.")
    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port, debug=False)
