/* ISPL Payroll console — front-end logic (vanilla, no build step). */
const $ = (s, r = document) => r.querySelector(s);
const api = (p) => fetch(p).then(r => r.json());

// Indian-format currency: 5,44,58,591  and a compact crore/lakh label.
const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
function money(n) { return n == null ? "—" : inr.format(Math.round(n)); }
function compactINR(n) {
  if (n == null) return "—";
  const a = Math.abs(n);
  if (a >= 1e7) return (n / 1e7).toFixed(2).replace(/\.00$/, "") + " Cr";
  if (a >= 1e5) return (n / 1e5).toFixed(2).replace(/\.00$/, "") + " L";
  return inr.format(Math.round(n));
}

const state = { period: null, status: "all", reason: "all", q: "", offset: 0, limit: 50, total: 0, periodStatus: "draft", locked: false, user: null, canWrite: false, canApprove: false, view: "actions" };
const LOCKED = new Set(["filed", "closed"]);
const RANK = { viewer: 0, clerk: 1, approver: 2, admin: 3 };
const FIGURE_LABELS = { gross_amt: "Gross", net_payable: "Net payable", excess_salary: "Excess salary" };

function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.classList.add("show");
  clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove("show"), 1800);
}

/* ---------- auth gate ---------- */
async function init() {
  const r = await fetch("/api/me");
  if (r.ok) { const d = await r.json(); enterApp(d.user); }
  else showLogin();
}

function showLogin() {
  $("#login-gate").hidden = false; $("#app").hidden = true;
  $("#login-form").onsubmit = async (e) => {
    e.preventDefault();
    const res = await fetch("/api/login", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: $("#login-user").value, password: $("#login-pass").value }),
    });
    if (res.ok) { const d = await res.json(); enterApp(d.user); }
    else { const e2 = $("#login-err"); e2.textContent = "Invalid username or password"; e2.hidden = false; }
  };
  $("#login-user").focus();
}

function enterApp(user) {
  state.user = user;
  state.canWrite = RANK[user.role] >= RANK.clerk;
  state.canApprove = RANK[user.role] >= RANK.approver;
  $("#login-gate").hidden = true; $("#app").hidden = false;

  // user chip
  $("#user-avatar").textContent = initials(user.full_name || user.username);
  $("#user-name").textContent = user.full_name || user.username;
  const rb = $("#user-role"); rb.textContent = user.role; rb.className = "role-badge " + user.role;
  $("#logout-btn").onclick = async () => { await fetch("/api/logout", { method: "POST" }); location.reload(); };

  // role gating (server also enforces — this just hides what won't work)
  $("#status-set").disabled = !state.canApprove;
  $("#status-set").title = state.canApprove ? "Change period status" : "Requires approver role";
  if (!state.canWrite) { $("#edit-by-fld") && ($("#edit-by-fld").hidden = true); }

  boot();
}
function initials(s) { return (s || "?").split(/\s+/).map(w => w[0]).slice(0, 2).join("").toUpperCase(); }

/* ---------- boot ---------- */
async function boot() {
  const periods = await api("/api/periods");
  const sel = $("#period-select");
  sel.innerHTML = periods.map(p => `<option value="${p.period}">${p.period}</option>`).join("");
  state.period = periods[0]?.period;
  sel.value = state.period;
  sel.onchange = () => { state.period = sel.value; state.offset = 0; loadAll(); };

  $("#status-filter").onclick = (e) => {
    const b = e.target.closest(".chip"); if (!b) return;
    [...$("#status-filter").children].forEach(c => c.classList.toggle("is-active", c === b));
    state.status = b.dataset.status; state.offset = 0; loadTable();
  };
  $("#view-switch").onclick = (e) => {
    const b = e.target.closest(".chip"); if (!b) return;
    [...$("#view-switch").children].forEach(c => c.classList.toggle("is-active", c === b));
    state.view = b.dataset.view; state.offset = 0;
    // status/reason filters only apply to the action list
    $("#status-filter").style.display = state.view === "actions" ? "" : "none";
    $("#reason-filter").style.display = state.view === "actions" ? "" : "none";
    loadTable();
  };
  $("#reason-filter").onchange = (e) => { state.reason = e.target.value; state.offset = 0; loadTable(); };
  let deb; $("#search").oninput = (e) => { clearTimeout(deb); deb = setTimeout(() => { state.q = e.target.value.trim(); state.offset = 0; loadTable(); }, 300); };
  $("#prev").onclick = () => { if (state.offset > 0) { state.offset -= state.limit; loadTable(); } };
  $("#next").onclick = () => { if (state.offset + state.limit < state.total) { state.offset += state.limit; loadTable(); } };

  $("#status-set").onchange = onStatusChange;
  $("#audit-btn").onclick = openAudit;
  $("#intake-btn").onclick = openIntake;
  $("#intake-close").onclick = () => $("#intake-back").hidden = true;
  $("#intake-back").onclick = (e) => { if (e.target.id === "intake-back") $("#intake-back").hidden = true; };
  $("#intake-month").onchange = loadIntake;
  $("#drawer-close").onclick = () => $("#drawer-back").hidden = true;
  $("#drawer-back").onclick = (e) => { if (e.target.id === "drawer-back") $("#drawer-back").hidden = true; };
  wireModal();

  await loadAll();
}

async function loadAll() {
  await Promise.all([loadSummary(), loadTable()]);
}

/* ---------- summary: golden rules + KPIs + charts ---------- */
async function loadSummary() {
  const d = await api("/api/summary?period=" + encodeURIComponent(state.period));
  const k = d.kpis || {}, run = d.run || {};

  // period status chip + lock state
  const st = (d.golden && d.golden.status) || k.status || "draft";
  state.periodStatus = st; state.locked = LOCKED.has(st);
  const chip = $("#period-status");
  chip.textContent = state.locked ? st + " 🔒" : st; chip.dataset.s = st;
  $("#status-set").value = st;

  // golden rules — LIVE (recomputed from current figures vs frozen anchors),
  // so a figure edit that breaks an invariant flips the badge immediately.
  const g = d.golden || {};
  $("#golden").innerHTML = [
    rule("PF gap", g.pf_gap ?? 0, "Σ Revised PF = ECR PF"),
    rule("Net drift", g.net_drift ?? 0, "Net payable never changes"),
    rule("ESI vs Future", g.esi_gap ?? 0, "Σ Revised ESIC = Future ESI"),
  ].join("");

  // KPIs
  $("#kpis").innerHTML = [
    kpi("a", "Net payable", compactINR(k.net_payable), money(k.net_payable) + " total", true),
    kpi("b", "Revised PF", compactINR(k.revised_pf), "ECR " + compactINR(k.ecr_pf), true),
    kpi("c", "Action rows", inr.format(k.action_rows || 0), (k.rows || 0) + " rows loaded", false),
    kpi("d", "Excess salary", compactINR(k.excess_salary), "flagged for review", true),
  ].join("");

  // charts
  barChart("#chart-reasons", (d.reasons || []).slice(0, 6).map(r => ({ name: r.reason, val: r.excess_salary })), compactINR);
  barChart("#chart-rules", (d.rule_mix || []).map(r => ({ name: r.rule, val: r.rows })), inr.format.bind(inr));
  donut("#chart-status", d.status_mix || []);

  // reason filter options
  const rf = $("#reason-filter");
  if (rf.options.length <= 1) {
    rf.innerHTML = `<option value="all">All reasons</option>` +
      (d.reasons || []).map(r => `<option value="${escapeAttr(r.reason)}">${escapeHtml(shorten(r.reason, 40))}</option>`).join("");
  }
}

function rule(name, v, sub) {
  const pass = Math.abs(v) <= 1;
  return `<div class="rule ${pass ? "pass" : "fail"}">
    <div class="dot">${pass ? "✓" : "!"}</div>
    <div><div class="k">${name} · ${sub}</div>
      <div class="v">${pass ? "PASS" : "REVIEW"} <small>${v === 0 ? "0" : money(v)}</small></div></div>
  </div>`;
}
function kpi(cls, label, value, meta, cur) {
  return `<div class="kpi ${cls}"><div class="label">${label}</div>
    <div class="value">${cur ? '<span class="cur">₹</span>' : ""}${value}</div>
    <div class="meta">${meta}</div></div>`;
}

/* ---------- charts ---------- */
function barChart(sel, data, fmt) {
  const max = Math.max(1, ...data.map(d => d.val || 0));
  $(sel).innerHTML = data.map((d, i) => `
    <div class="bar-row">
      <span class="name" title="${escapeAttr(d.name || "")}">${escapeHtml(shorten(d.name || "", 34))}</span>
      <span class="val">${fmt(d.val || 0)}</span>
      <span class="bar-track"><span class="bar-fill c${i % 6}" style="width:${(100 * (d.val || 0) / max).toFixed(1)}%"></span></span>
    </div>`).join("") || `<div class="card-note">No data</div>`;
}

function donut(sel, mix) {
  const order = ["open", "investigating", "resolved", "waived"];
  const map = Object.fromEntries(mix.map(m => [m.status, +m.items]));
  const total = order.reduce((s, k) => s + (map[k] || 0), 0) || 1;
  const colors = { open: "#fab219", investigating: "#2a78d6", resolved: "#0ca30c", waived: "#8a8d99" };
  let acc = 0; const R = 60, C = 2 * Math.PI * R, segs = [];
  order.forEach(k => {
    const v = map[k] || 0; if (!v) return;
    const len = C * v / total;
    segs.push(`<circle r="${R}" cx="74" cy="74" fill="none" stroke="${colors[k]}" stroke-width="20"
      stroke-dasharray="${len} ${C - len}" stroke-dashoffset="${-acc}" transform="rotate(-90 74 74)"/>`);
    acc += len;
  });
  const svg = `<svg class="donut" viewBox="0 0 148 148">${segs.join("")}
    <text x="74" y="70" text-anchor="middle" font-size="26" font-weight="720" fill="#0b0b0e">${total}</text>
    <text x="74" y="90" text-anchor="middle" font-size="11" fill="#8a8d99">tickets</text></svg>`;
  const legend = `<div class="legend">${order.map(k =>
    `<div class="li"><span class="sw ${k}"></span>${k[0].toUpperCase() + k.slice(1)}<span class="n">${map[k] || 0}</span></div>`).join("")}</div>`;
  $(sel).innerHTML = svg + legend;
}

/* ---------- action list / salary register table ---------- */
const HEAD_ACTIONS = `<tr><th>Employee</th><th>Site</th><th>Rule</th>
  <th class="num">Gross</th><th class="num">Net</th><th class="num">Excess ₹</th>
  <th>Reason</th><th>Status</th><th>Owner</th></tr>`;
const HEAD_REGISTER = `<tr><th>Employee</th><th>Site</th><th>Rule</th>
  <th class="num">Days</th><th class="num">Gross</th><th class="num">Revised gross</th>
  <th class="num">PF</th><th class="num">ESIC</th><th class="num">Net</th><th>Flag</th></tr>`;

async function loadTable() {
  const hint = state.locked ? ` &nbsp;<span class="locked-note">🔒 ${state.periodStatus} — figures locked</span>`
    : state.canWrite ? ` &nbsp;<span class="card-note">· click a Gross / Net cell to correct</span>`
    : ` &nbsp;<span class="card-note">· read-only (viewer)</span>`;
  const from_ = (total) => total ? state.offset + 1 : 0;

  if (state.view === "register") {
    $("#table-head").innerHTML = HEAD_REGISTER;
    const p = new URLSearchParams({ period: state.period, q: state.q, limit: state.limit, offset: state.offset });
    const d = await api("/api/register?" + p.toString());
    state.total = d.total;
    $("#table-count").innerHTML = `${inr.format(d.total)} employees — full salary register` + hint;
    $("#rows").innerHTML = d.rows.map(registerRowHtml).join("") ||
      `<tr><td colspan="10" style="text-align:center;padding:26px;color:var(--muted)">No matching employees</td></tr>`;
    wireRowEdits();
    $("#pageinfo").textContent = `${from_(d.total)}–${Math.min(state.offset + state.limit, d.total)} of ${inr.format(d.total)}`;
  } else {
    $("#table-head").innerHTML = HEAD_ACTIONS;
    const p = new URLSearchParams({ period: state.period, status: state.status, reason: state.reason, q: state.q, limit: state.limit, offset: state.offset });
    const d = await api("/api/actions?" + p.toString());
    state.total = d.total;
    $("#table-count").innerHTML = `${inr.format(d.total)} tickets` + hint;
    $("#rows").innerHTML = d.rows.map(rowHtml).join("") ||
      `<tr><td colspan="9" style="text-align:center;padding:26px;color:var(--muted)">No matching tickets</td></tr>`;
    wireRow();
    wireRowEdits();
    $("#pageinfo").textContent = `${from_(d.total)}–${Math.min(state.offset + state.limit, d.total)} of ${inr.format(d.total)}`;
  }
  $("#prev").disabled = state.offset === 0;
  $("#next").disabled = state.offset + state.limit >= state.total;
}

function registerRowHtml(r) {
  const ed = (state.locked || !state.canWrite) ? "" : "editable";
  const cell = (field, val, extra = "") =>
    `<td class="num ${extra} ${ed}" ${ed ? `data-rid="${r.payroll_row_id}" data-field="${field}" data-val="${val ?? ""}" data-emp="${escapeAttr(r.full_name || r.emp_code)}"` : ""}>${money(val)}</td>`;
  const d0 = r.normal_days != null ? Math.round(r.normal_days) : "—";
  const days = `${d0}${r.adj_working_days != null ? " / " + Math.round(r.adj_working_days) : ""}`;
  return `<tr data-id="reg-${r.payroll_row_id}">
    <td><div class="emp-name">${escapeHtml(r.full_name || "")}</div><div class="emp-code">${r.emp_code}</div></td>
    <td><div>${escapeHtml(shorten(r.site_name || "", 24))}</div><div class="site-state">${escapeHtml(r.site_state || "")}</div></td>
    <td><span class="tag">${r.rule_applied || "—"}</span></td>
    <td class="num" title="worked / adjusted days">${days}</td>
    ${cell("gross_amt", r.gross_amt)}
    <td class="num">${money(r.revised_gross)}</td>
    <td class="num">${money(r.revised_pf)}</td>
    <td class="num">${money(r.revised_esic)}</td>
    ${cell("net_payable", r.net_payable)}
    <td>${r.action_needed ? '<span class="tag tag-flag">ESI</span>' : ""}</td>
  </tr>`;
}

function rowHtml(r) {
  const statuses = ["open", "investigating", "resolved", "waived"];
  const ed = (state.locked || !state.canWrite) ? "" : "editable";
  const cell = (field, val, extra = "") =>
    `<td class="num ${extra} ${ed}" ${ed ? `data-rid="${r.payroll_row_id || r.id}" data-field="${field}" data-val="${val ?? ""}" data-emp="${escapeAttr(r.full_name || r.emp_code)}"` : ""}>${money(val)}</td>`;
  return `<tr data-id="${r.id}">
    <td><div class="emp-name">${escapeHtml(r.full_name || "")}</div><div class="emp-code">${r.emp_code}</div></td>
    <td><div>${escapeHtml(shorten(r.site_name || "", 26))}</div><div class="site-state">${escapeHtml(r.site_state || "")}</div></td>
    <td><span class="tag">${r.rule_applied || "—"}</span></td>
    ${cell("gross_amt", r.gross_amt)}
    ${cell("net_payable", r.net_payable)}
    ${cell("excess_salary", r.excess_salary, "excess")}
    <td class="reason-cell">${escapeHtml(shorten(r.reason || "", 60))}</td>
    <td><select class="st-select st-${r.status}" data-role="status">
      ${statuses.map(s => `<option value="${s}" ${s === r.status ? "selected" : ""}>${s[0].toUpperCase() + s.slice(1)}</option>`).join("")}
    </select></td>
    <td><input class="owner-input" data-role="owner" value="${escapeAttr(r.assigned_to || "")}" placeholder="assign…"></td>
  </tr>`;
}

function wireRow() {
  $("#rows").querySelectorAll("tr[data-id]").forEach(tr => {
    const id = tr.dataset.id;
    const sel = tr.querySelector('[data-role="status"]');
    const owner = tr.querySelector('[data-role="owner"]');
    if (!state.canWrite) { sel.disabled = true; owner.disabled = true; return; }
    sel.onchange = async () => {
      sel.className = "st-select st-" + sel.value;
      await patch(id, { status: sel.value });
      toast("Status → " + sel.value);
      loadSummary(); // refresh donut / status counts
    };
    owner.onchange = async () => { await patch(id, { assigned_to: owner.value }); toast("Owner saved"); };
  });
}

function patch(id, body) {
  return fetch("/api/actions/" + id, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  }).then(r => r.json());
}

/* ---------- edit a figure (click cell → modal) ---------- */
let editCtx = null;
function wireRowEdits() {
  $("#rows").querySelectorAll("td.editable").forEach(td => {
    td.onclick = () => openEdit(td.dataset);
  });
}
function openEdit(ds) {
  if (state.locked) { toast("Period is " + state.periodStatus + " — figures are locked"); return; }
  editCtx = { rid: ds.rid, field: ds.field };
  $("#edit-title").textContent = "Correct " + (FIGURE_LABELS[ds.field] || ds.field);
  $("#edit-ctx").innerHTML = `<b>${escapeHtml(ds.emp)}</b> · ${state.period} · current value <b>₹${money(+ds.val)}</b>`;
  $("#edit-field-label").textContent = "New " + (FIGURE_LABELS[ds.field] || ds.field) + " (₹)";
  $("#edit-value").value = ds.val || "";
  $("#edit-reason").value = "";
  $("#edit-as").textContent = "Signed as " + (state.user.full_name || state.user.username) + " · this change is audited";
  $("#edit-back").hidden = false;
  $("#edit-value").focus();
}
function wireModal() {
  $("#edit-cancel").onclick = () => $("#edit-back").hidden = true;
  $("#edit-back").onclick = (e) => { if (e.target.id === "edit-back") $("#edit-back").hidden = true; };
  $("#edit-save").onclick = saveEdit;
}
async function saveEdit() {
  const reason = $("#edit-reason").value.trim();
  if (!reason) { toast("A reason is required"); $("#edit-reason").focus(); return; }
  const res = await fetch("/api/payroll/" + editCtx.rid, {
    method: "PATCH", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ field: editCtx.field, value: $("#edit-value").value, reason }),
  }).then(r => r.json().then(j => ({ ok: r.ok, j })));
  if (!res.ok) { toast(res.j.error || "Edit failed"); return; }
  $("#edit-back").hidden = true;
  toast("Saved · change audited");
  await loadAll(); // refresh figures + LIVE golden badges
}

/* ---------- period status ---------- */
async function onStatusChange(e) {
  const next = e.target.value;
  let reason = "";
  if (LOCKED.has(state.periodStatus) && !LOCKED.has(next)) {
    reason = prompt(`Reopening a ${state.periodStatus} period. Reason (required):`) || "";
    if (!reason.trim()) { e.target.value = state.periodStatus; toast("Reopen cancelled — reason required"); return; }
  }
  const res = await fetch(`/api/periods/${encodeURIComponent(state.period)}/status`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: next, reason }),
  }).then(r => r.json().then(j => ({ ok: r.ok, j })));
  if (!res.ok) { toast(res.j.error || "Failed"); e.target.value = state.periodStatus; return; }
  toast("Period → " + next);
  await loadAll();
}

/* ---------- audit drawer ---------- */
async function openAudit() {
  $("#drawer-back").hidden = false;
  const d = await api("/api/audit?period=" + encodeURIComponent(state.period));
  $("#audit-list").innerHTML = (d.rows || []).map(a => {
    const who = escapeHtml(a.full_name || a.emp_code || (a.entity === "salary_period" ? "period" : ""));
    const when = new Date(a.changed_at).toLocaleString("en-IN");
    const fld = a.field === "status" ? "status" : (FIGURE_LABELS[a.field] || a.field);
    const fmt = a.field === "status" ? (v) => v : (v) => v == null ? "—" : "₹" + money(+v);
    return `<div class="audit-item">
      <div class="top"><span class="who">${who}</span><span class="when">${when}</span></div>
      <div class="chg"><span class="f">${fld}</span>: <span class="old">${escapeHtml(fmt(a.old_value))}</span>
        → <span class="new">${escapeHtml(fmt(a.new_value))}</span></div>
      <div class="rsn">“${escapeHtml(a.reason || "")}”${a.changed_by ? " — " + escapeHtml(a.changed_by) : ""}</div>
    </div>`;
  }).join("") || `<div class="audit-empty">No changes recorded for ${state.period} yet.</div>`;
}

/* ---------- monthly intake ---------- */
function openIntake() { $("#intake-back").hidden = false; loadIntake(); }

async function loadIntake() {
  const period = $("#intake-month").value; // 'YYYY-MM'
  if (!period) return;
  const d = await api("/api/intake?period=" + encodeURIComponent(period));
  $("#intake-fy").textContent = d.fy || "—";

  // PRIMARY: upload the processed file (gated by role only, not raw inputs)
  const r = $("#intake-recon");
  if (!state.canApprove) {
    r.innerHTML = `<div class="recon-gate">An <b>approver</b> loads a month's processed reconciliation file.</div>`;
  } else {
    const exists = d.has_rows;
    r.innerHTML = `${exists ? `<div class="recon-gate">${period} is already loaded. Uploading again <b>replaces</b> its rows as a new audited run.</div>` : ""}
      <label class="fld"><span>Processed reconciliation file (reconcile.py output CSV)</span><input type="file" id="recon-file" accept=".csv"></label>
      <button class="btn btn-primary" id="recon-run">${exists ? "Replace month" : "Load month"}</button>`;
    $("#recon-run").onclick = () => runReconcile(period);
  }

  // OPTIONAL: raw-input readiness board (collapsed by default)
  $("#intake-slots").innerHTML = d.slots.map(s => {
    const got = s.received, L = got ? "received" : "pending";
    const meta = got ? `Uploaded by <b>${escapeHtml(s.latest.uploaded_by)}</b> · ${new Date(s.latest.uploaded_at).toLocaleString("en-IN")}<br><span class="card-note">${escapeHtml(s.latest.filename)}</span>`
                     : `Waiting on: ${escapeHtml(s.owners.join(", ") || "—")}`;
    const control = s.may_upload
      ? `<div class="slot-upload"><input type="file" data-type="${s.input_type}"><button class="btn" data-up="${s.input_type}">${got ? "Replace" : "Upload"}</button></div>`
      : (got ? "" : `<div class="slot-locked">Only ${escapeHtml(s.owners.join(", ") || "the owner")} can upload this.</div>`);
    return `<div class="slot">
      <div class="slot-head"><div class="slot-dot ${L}">${got ? "✓" : "•"}</div>
        <div><div class="slot-title">${escapeHtml(s.label)}</div><div class="slot-owners">owners: ${escapeHtml(s.owners.join(", ") || "—")}</div></div>
        <div class="slot-state ${L}">${got ? "RECEIVED" : "PENDING"}</div></div>
      <div class="slot-meta">${meta}</div>${control}</div>`;
  }).join("");
  $("#intake-slots").querySelectorAll("[data-up]").forEach(btn => btn.onclick = () => uploadInput(period, btn.dataset.up));
}

async function uploadInput(period, type) {
  const inp = $(`#intake-slots input[data-type="${type}"]`);
  if (!inp.files.length) { toast("Choose a file first"); return; }
  const fd = new FormData(); fd.append("file", inp.files[0]);
  const res = await fetch(`/api/intake/${encodeURIComponent(period)}/${type}`, { method: "POST", body: fd })
    .then(r => r.json().then(j => ({ ok: r.ok, j })));
  if (!res.ok) { toast(res.j.error || "Upload failed"); return; }
  toast(res.j.filename + " uploaded"); loadIntake(); refreshPeriods();
}

async function runReconcile(period) {
  const f = $("#recon-file");
  if (!f.files.length) { toast("Attach the processed reconciliation file"); return; }
  const fd = new FormData(); fd.append("file", f.files[0]);
  toast("Loading reconciled result…");
  const res = await fetch(`/api/reconcile/${encodeURIComponent(period)}`, { method: "POST", body: fd })
    .then(r => r.json().then(j => ({ ok: r.ok, j })));
  if (!res.ok) { toast(res.j.error || "Reconciliation failed"); return; }
  const c = res.j.checks;
  toast(`${period} reconciled — ${inr.format(res.j.rows)} rows, PF gap ${c.rule1_pass ? "0 ✓" : "REVIEW"}`);
  await refreshPeriods(period);
  $("#intake-back").hidden = true;
}

async function refreshPeriods(select) {
  const periods = await api("/api/periods");
  const sel = $("#period-select");
  sel.innerHTML = periods.map(p => `<option value="${p.period}">${p.period}</option>`).join("");
  state.period = select || state.period || periods[0]?.period;
  sel.value = state.period;
  await loadAll();
}

/* ---------- utils ---------- */
function shorten(s, n) { return s && s.length > n ? s.slice(0, n - 1) + "…" : s; }
function escapeHtml(s) { return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function escapeAttr(s) { return escapeHtml(s); }

init();
