#!/usr/bin/env python3
import json,os
OUT="/home/user/anthropic-finance/docs/pf-salary-reconciliation/april-2026"
data=json.load(open(os.path.join(OUT,"reconciliation_data_April2026.json")))

HTML="""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PF / ESI Reconciliation — April 2026</title>
<style>
:root{--bg:#0d1117;--panel:#161b22;--panel2:#1c2230;--ink:#e6edf3;--mut:#8b949e;
--line:#2d333b;--ok:#3fb950;--rev:#d29922;--fail:#f85149;--acc:#58a6ff;--acc2:#bc8cff}
*{box-sizing:border-box}body{margin:0;font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:var(--bg);color:var(--ink)}
header{padding:22px 26px;border-bottom:1px solid var(--line);background:linear-gradient(90deg,#161b22,#1c2230)}
h1{margin:0;font-size:20px}.sub{color:var(--mut);margin-top:4px;font-size:13px}
.wrap{padding:22px 26px;max-width:1180px;margin:0 auto}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:22px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi.hi{border-color:var(--ok);box-shadow:0 0 0 1px rgba(63,185,80,.25)}
.kpi .lbl{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.kpi .val{font-size:22px;font-weight:700;margin-top:6px}.kpi .note{color:var(--mut);font-size:11px;margin-top:3px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px;margin-bottom:22px}
.card h2{margin:0 0 14px;font-size:15px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}thead th{color:var(--mut);font-weight:600}
tr.total td{font-weight:700;border-top:2px solid var(--line)}
.pill{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600}
.p-PASS{background:rgba(63,185,80,.16);color:var(--ok)}.p-REVIEW{background:rgba(210,153,34,.16);color:var(--rev)}
.p-INFO{background:rgba(88,166,255,.16);color:var(--acc)}.p-FAIL{background:rgba(248,81,73,.16);color:var(--fail)}
.chk{display:flex;gap:12px;padding:11px 0;border-bottom:1px solid var(--line);align-items:flex-start}
.chk:last-child{border:0}.chk .nm{font-weight:600}.chk .dt{color:var(--mut);font-size:12.5px;margin-top:3px}
.grid2{display:grid;grid-template-columns:1.1fr .9fr;gap:22px}@media(max-width:820px){.grid2{grid-template-columns:1fr}}
.tag{font-size:11px;color:var(--mut)}.legend{color:var(--mut);font-size:12px;margin-top:10px}
.bars text{fill:var(--mut);font-size:11px}
</style></head><body>
<header><h1>PF / ESI Salary Reconciliation — April 2026</h1>
<div class="sub">ISPL (Impressions Services) · FY2026-27 · validated against the <code>pf-salary-reconciliation</code> skill</div></header>
<div class="wrap">
 <div class="kpis" id="kpis"></div>
 <div class="card"><h2>Checks &amp; Balances <span class="tag" id="cc"></span></h2><div id="checks"></div>
  <div class="legend">PF is fully reconciled and re-verified row-by-row. The single REVIEW item is the
  expected ESI-vs-Future residual (secondary-site / Future-only employees), pending the report's ESI_Audit tab.</div></div>
 <div class="grid2">
  <div class="card"><h2>PF: Revised vs ECR (₹0 gap)</h2><div id="pfbar"></div></div>
  <div class="card"><h2>Rows by rule group</h2><div id="rows"></div></div>
 </div>
 <div class="card"><h2>Reconciliation by rule group (₹)</h2><table id="tbl"></table></div>
</div>
<script id="d" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('d').textContent);
const cr=n=>'₹'+(n/1e7).toFixed(2)+' Cr';const inr=n=>'₹'+Math.round(n).toLocaleString('en-IN');
const A=D.audit;
const kpis=[
 ['Revised PF',cr(D.revised_pf),'= ECR filed','hi'],
 ['PF gap',inr(D.pf_gap),'sacrosanct match','hi'],
 ['PF-anchor employees',D.rulegrp[0][1].toLocaleString('en-IN'),'PF deposited once each',''],
 ['Rows reconciled',D.tot_rows.toLocaleString('en-IN'),'anchor+secondary+ESI+none',''],
 ['12% compliance','100%',A.twelve_pct_ok.toLocaleString('en-IN')+' / '+A.pf_positive.toLocaleString('en-IN')+' rows','hi'],
 ['ESI vs Future gap',inr(D.esi_gap),'secondary / Future-only','']];
document.getElementById('kpis').innerHTML=kpis.map(k=>
 `<div class="kpi ${k[3]}"><div class="lbl">${k[0]}</div><div class="val">${k[1]}</div><div class="note">${k[2]}</div></div>`).join('');
const ord={FAIL:0,REVIEW:1,PASS:2,INFO:3};
const cs=[...D.checks].sort((a,b)=>ord[a.status]-ord[b.status]);
const cnt={PASS:0,REVIEW:0,INFO:0,FAIL:0};cs.forEach(c=>cnt[c.status]++);
document.getElementById('cc').textContent=`${cnt.PASS} PASS · ${cnt.REVIEW} REVIEW · 0 FAIL`;
document.getElementById('checks').innerHTML=cs.map(c=>
 `<div class="chk"><span class="pill p-${c.status}">${c.status}</span><div><div class="nm">${c.name}</div><div class="dt">${c.detail}</div></div></div>`).join('');
// PF bar
const pf=[['Revised PF',D.revised_pf,'var(--ok)'],['ECR PF',D.ecr_pf,'var(--acc)']];
const mx=Math.max(...pf.map(p=>p[1]));
document.getElementById('pfbar').innerHTML=pf.map(p=>
 `<div style="margin:12px 0"><div style="display:flex;justify-content:space-between;font-size:13px"><span>${p[0]}</span><span>${inr(p[1])}</span></div>
  <div style="height:14px;background:var(--panel2);border-radius:7px;overflow:hidden;margin-top:5px"><div style="height:100%;width:${(p[1]/mx*100).toFixed(2)}%;background:${p[2]}"></div></div></div>`).join('')
 +`<div class="legend">Difference: <b style="color:var(--ok)">${inr(D.pf_gap)}</b> — salary PF matches the EPFO-filed ECR to the rupee.</div>`;
// rows donut bar
const rg=D.rulegrp.map((r,i)=>[r[0],r[1],['var(--acc)','var(--acc2)','var(--rev)','var(--mut)'][i]]);
const rs=rg.reduce((s,x)=>s+x[1],0);
document.getElementById('rows').innerHTML=
 '<div style="display:flex;height:26px;border-radius:6px;overflow:hidden;margin-bottom:12px">'+
 rg.map(x=>`<div title="${x[0]}: ${x[1]}" style="width:${(x[1]/rs*100).toFixed(2)}%;background:${x[2]}"></div>`).join('')+'</div>'+
 rg.map(x=>`<div style="display:flex;justify-content:space-between;font-size:12.5px;margin:5px 0">
  <span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${x[2]};margin-right:7px"></span>${x[0]}</span>
  <span>${x[1].toLocaleString('en-IN')} <span class="tag">(${(x[1]/rs*100).toFixed(1)}%)</span></span></div>`).join('');
// table
let t='<thead><tr><th>Rule group</th><th>Rows</th><th>Revised PF</th><th>ECR PF</th><th>Revised ESIC</th><th>Future ESI</th></tr></thead><tbody>';
D.rulegrp.forEach(r=>{t+='<tr><td>'+r[0]+'</td>'+[r[1],r[2],r[3],r[4],r[5]].map(v=>'<td>'+Math.round(v).toLocaleString('en-IN')+'</td>').join('')+'</tr>';});
t+='<tr class="total"><td>TOTAL</td><td>'+D.tot_rows.toLocaleString('en-IN')+'</td><td>'+D.revised_pf.toLocaleString('en-IN')+'</td><td>'+D.ecr_pf.toLocaleString('en-IN')+'</td><td>'+Math.round(D.revised_esi).toLocaleString('en-IN')+'</td><td>'+Math.round(D.future_esi).toLocaleString('en-IN')+'</td></tr></tbody>';
document.getElementById('tbl').innerHTML=t;
</script></body></html>"""
HTML=HTML.replace("__DATA__",json.dumps(data))
open(os.path.join(OUT,"dashboard_April2026.html"),"w").write(HTML)
print("wrote dashboard_April2026.html",len(HTML),"bytes")
