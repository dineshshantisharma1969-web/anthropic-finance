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

const state = { period: null, status: "all", reason: "all", q: "", offset: 0, limit: 50, total: 0, periodStatus: "draft", locked: false, by: "" };
const LOCKED = new Set(["filed", "closed"]);
const FIGURE_LABELS = { gross_amt: "Gross", net_payable: "Net payable", excess_salary: "Excess salary" };

function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.classList.add("show");
  clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove("show"), 1800);
}

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
  $("#reason-filter").onchange = (e) => { state.reason = e.target.value; state.offset = 0; loadTable(); };
  let deb; $("#search").oninput = (e) => { clearTimeout(deb); deb = setTimeout(() => { state.q = e.target.value.trim(); state.offset = 0; loadTable(); }, 300); };
  $("#prev").onclick = () => { if (state.offset > 0) { state.offset -= state.limit; loadTable(); } };
  $("#next").onclick = () => { if (state.offset + state.limit < state.total) { state.offset += state.limit; loadTable(); } };

  $("#status-set").onchange = onStatusChange;
  $("#audit-btn").onclick = openAudit;
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

/* ---------- action table ---------- */
async function loadTable() {
  const p = new URLSearchParams({ period: state.period, status: state.status, reason: state.reason, q: state.q, limit: state.limit, offset: state.offset });
  const d = await api("/api/actions?" + p.toString());
  state.total = d.total;
  $("#table-count").innerHTML = `${inr.format(d.total)} tickets` +
    (state.locked ? ` &nbsp;<span class="locked-note">🔒 ${state.periodStatus} — figures locked</span>`
                  : ` &nbsp;<span class="card-note">· click a Gross / Net / Excess cell to correct</span>`);
  $("#rows").innerHTML = d.rows.map(rowHtml).join("") ||
    `<tr><td colspan="9" style="text-align:center;padding:26px;color:var(--muted)">No matching tickets</td></tr>`;
  wireRow();
  wireRowEdits();
  const from = d.total ? state.offset + 1 : 0, to = Math.min(state.offset + state.limit, d.total);
  $("#pageinfo").textContent = `${from}–${to} of ${inr.format(d.total)}`;
  $("#prev").disabled = state.offset === 0;
  $("#next").disabled = state.offset + state.limit >= d.total;
}

function rowHtml(r) {
  const statuses = ["open", "investigating", "resolved", "waived"];
  const ed = state.locked ? "" : "editable";
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
    sel.onchange = async () => {
      sel.className = "st-select st-" + sel.value;
      await patch(id, { status: sel.value });
      toast("Status → " + sel.value);
      loadSummary(); // refresh donut / status counts
    };
    const owner = tr.querySelector('[data-role="owner"]');
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
  $("#edit-by").value = state.by || "";
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
  state.by = $("#edit-by").value.trim();
  const res = await fetch("/api/payroll/" + editCtx.rid, {
    method: "PATCH", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ field: editCtx.field, value: $("#edit-value").value, reason, changed_by: state.by || "unknown" }),
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
    body: JSON.stringify({ status: next, reason, changed_by: state.by || "unknown" }),
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

/* ---------- utils ---------- */
function shorten(s, n) { return s && s.length > n ? s.slice(0, n - 1) + "…" : s; }
function escapeHtml(s) { return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function escapeAttr(s) { return escapeHtml(s); }

boot();
