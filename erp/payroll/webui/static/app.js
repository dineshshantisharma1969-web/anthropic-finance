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

const state = { period: null, status: "all", reason: "all", q: "", offset: 0, limit: 50, total: 0 };

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

  await loadAll();
}

async function loadAll() {
  await Promise.all([loadSummary(), loadTable()]);
}

/* ---------- summary: golden rules + KPIs + charts ---------- */
async function loadSummary() {
  const d = await api("/api/summary?period=" + encodeURIComponent(state.period));
  const k = d.kpis || {}, run = d.run || {};

  // period status chip
  const chip = $("#period-status");
  chip.textContent = k.status || "—"; chip.dataset.s = k.status || "draft";

  // golden rules
  const pfGap = run.pf_gap ?? 0, netDrift = run.net_drift ?? 0;
  const esiGap = (run.checks && run.checks.esi_future_gap) ?? 0;
  $("#golden").innerHTML = [
    rule("PF gap", pfGap, "Σ Revised PF = ECR PF"),
    rule("Net drift", netDrift, "Net payable never changes"),
    rule("ESI vs Future", esiGap, "Σ Revised ESIC = Future ESI"),
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
  $("#table-count").textContent = `${inr.format(d.total)} tickets`;
  $("#rows").innerHTML = d.rows.map(rowHtml).join("") ||
    `<tr><td colspan="9" style="text-align:center;padding:26px;color:var(--muted)">No matching tickets</td></tr>`;
  wireRow();
  const from = d.total ? state.offset + 1 : 0, to = Math.min(state.offset + state.limit, d.total);
  $("#pageinfo").textContent = `${from}–${to} of ${inr.format(d.total)}`;
  $("#prev").disabled = state.offset === 0;
  $("#next").disabled = state.offset + state.limit >= d.total;
}

function rowHtml(r) {
  const statuses = ["open", "investigating", "resolved", "waived"];
  return `<tr data-id="${r.id}">
    <td><div class="emp-name">${escapeHtml(r.full_name || "")}</div><div class="emp-code">${r.emp_code}</div></td>
    <td><div>${escapeHtml(shorten(r.site_name || "", 26))}</div><div class="site-state">${escapeHtml(r.site_state || "")}</div></td>
    <td><span class="tag">${r.rule_applied || "—"}</span></td>
    <td class="num">${money(r.gross_amt)}</td>
    <td class="num">${money(r.net_payable)}</td>
    <td class="num excess">${money(r.excess_salary)}</td>
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

/* ---------- utils ---------- */
function shorten(s, n) { return s && s.length > n ? s.slice(0, n - 1) + "…" : s; }
function escapeHtml(s) { return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function escapeAttr(s) { return escapeHtml(s); }

boot();
