/* HealthSnap demo charts — dependency-free SVG.
   Series colors are validated for the #0F1117 surface (OKLCH L 0.48–0.67,
   CVD-safe adjacent pairs): green #009E70, amber #BD8600, purple #7A5CEE,
   coral #D63E4C. Neon brand colors are reserved for UI accents. */

const CH = { green: "#009E70", amber: "#BD8600", purple: "#7A5CEE", coral: "#D63E4C" };
const GRID = "#1E2A3A", AXIS = "#64748B";

const svgNS = "http://www.w3.org/2000/svg";
function el(name, attrs, parent) {
  const n = document.createElementNS(svgNS, name);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(n);
  return n;
}

function makeTip(box) {
  const tip = document.createElement("div");
  tip.className = "tip";
  box.appendChild(tip);
  return tip;
}
function showTip(tip, box, x, y, html) {
  tip.innerHTML = html;
  tip.style.display = "block";
  const bw = box.clientWidth, tw = tip.offsetWidth;
  let left = x + 14;
  if (left + tw > bw - 4) left = x - tw - 14;
  tip.style.left = Math.max(4, left) + "px";
  tip.style.top = Math.max(4, y - tip.offsetHeight / 2) + "px";
}

/* Rounded-top bar path anchored to the baseline (4px radius). */
function barPath(x, y, w, h, r) {
  r = Math.min(r, w / 2, h);
  return `M${x},${y + h} L${x},${y + r} Q${x},${y} ${x + r},${y} L${x + w - r},${y} Q${x + w},${y} ${x + w},${y + r} L${x + w},${y + h} Z`;
}

/* ---- Calorie donut (hero number, single value) ---- */
function calorieRing(sel, eaten, target) {
  const host = document.querySelector(sel);
  const size = 132, sw = 11, r = (size - sw) / 2, c = 2 * Math.PI * r;
  const pct = Math.min(eaten / target, 1);
  const svg = el("svg", { viewBox: `0 0 ${size} ${size}`, width: size, height: size, role: "img",
    "aria-label": `${eaten} of ${target} kilocalories today` });
  el("circle", { cx: size/2, cy: size/2, r, fill: "none", stroke: GRID, "stroke-width": sw }, svg);
  el("circle", { cx: size/2, cy: size/2, r, fill: "none", stroke: CH.green, "stroke-width": sw,
    "stroke-linecap": "round", "stroke-dasharray": `${c * pct} ${c}`,
    transform: `rotate(-90 ${size/2} ${size/2})` }, svg);
  const t1 = el("text", { x: size/2, y: size/2 - 2, "text-anchor": "middle", fill: "#F1F5F9",
    "font-size": "24", "font-weight": "800" }, svg);
  t1.textContent = eaten.toLocaleString("en-IN");
  const t2 = el("text", { x: size/2, y: size/2 + 18, "text-anchor": "middle", fill: "#64748B",
    "font-size": "10.5", "font-weight": "600" }, svg);
  t2.textContent = `of ${target.toLocaleString("en-IN")} kcal`;
  host.appendChild(svg);
}

/* ---- Bar chart: one series + optional target line ---- */
function barChart(sel, labels, values, opts) {
  const { color = CH.green, target = null, unit = "kcal", name = "Calories" } = opts || {};
  const box = document.querySelector(sel);
  const W = 640, H = 240, pad = { t: 18, r: 12, b: 26, l: 40 };
  const iw = W - pad.l - pad.r, ih = H - pad.t - pad.b;
  const max = Math.max(...values, target || 0) * 1.15;
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": name + " chart" });
  box.appendChild(svg);
  const tip = makeTip(box);

  const ticks = 4;
  for (let i = 0; i <= ticks; i++) {
    const v = (max / ticks) * i, y = pad.t + ih - (v / max) * ih;
    el("line", { x1: pad.l, x2: W - pad.r, y1: y, y2: y, stroke: GRID, "stroke-width": 1 }, svg);
    const t = el("text", { x: pad.l - 6, y: y + 3.5, "text-anchor": "end", fill: AXIS, "font-size": 10 }, svg);
    t.textContent = Math.round(v);
  }

  const n = values.length, slot = iw / n, bw = Math.min(34, slot - 8);
  values.forEach((v, i) => {
    const x = pad.l + i * slot + (slot - bw) / 2;
    const h = Math.max((v / max) * ih, 2), y = pad.t + ih - h;
    const p = el("path", { d: barPath(x, y, bw, h, 4), fill: color }, svg);
    // hit target bigger than the mark
    const hit = el("rect", { x: pad.l + i * slot, y: pad.t, width: slot, height: ih, fill: "transparent" }, svg);
    const lbl = el("text", { x: pad.l + i * slot + slot / 2, y: H - 8, "text-anchor": "middle",
      fill: AXIS, "font-size": 10.5, "font-weight": 600 }, svg);
    lbl.textContent = labels[i];
    hit.addEventListener("mousemove", (e) => {
      const r = box.getBoundingClientRect();
      p.setAttribute("fill", "#00c98d");
      showTip(tip, box, e.clientX - r.left, e.clientY - r.top,
        `<b>${labels[i]}</b><div class="row"><i class="sw" style="background:${color}"></i>${v.toLocaleString("en-IN")} ${unit}</div>` +
        (target ? `<div class="row" style="color:#64748B">target ${target.toLocaleString("en-IN")}</div>` : ""));
    });
    hit.addEventListener("mouseleave", () => { p.setAttribute("fill", color); tip.style.display = "none"; });
  });

  if (target) {
    const ty = pad.t + ih - (target / max) * ih;
    el("line", { x1: pad.l, x2: W - pad.r, y1: ty, y2: ty, stroke: CH.coral,
      "stroke-width": 2, "stroke-dasharray": "6 4" }, svg);
    const t = el("text", { x: W - pad.r, y: ty - 5, "text-anchor": "end", fill: "#FF6B6B",
      "font-size": 10.5, "font-weight": 700 }, svg);
    t.textContent = `target ${target.toLocaleString("en-IN")}`;
  }
}

/* ---- Multi-line chart with normal-range band + crosshair tooltip ---- */
function lineChart(sel, labels, series, opts) {
  const { band = null, unit = "", ymin = null, ymax = null } = opts || {};
  const box = document.querySelector(sel);
  const W = 640, H = 250, pad = { t: 14, r: 14, b: 26, l: 38 };
  const iw = W - pad.l - pad.r, ih = H - pad.t - pad.b;
  const all = series.flatMap(s => s.values);
  const lo = ymin !== null ? ymin : Math.min(...all, band ? band[0] : Infinity) * 0.92;
  const hi = ymax !== null ? ymax : Math.max(...all, band ? band[1] : -Infinity) * 1.06;
  const X = i => pad.l + (i / (labels.length - 1)) * iw;
  const Y = v => pad.t + ih - ((v - lo) / (hi - lo)) * ih;

  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" }, undefined);
  box.appendChild(svg);
  const tip = makeTip(box);

  if (band) {
    el("rect", { x: pad.l, y: Y(band[1]), width: iw, height: Y(band[0]) - Y(band[1]),
      fill: "rgba(0,158,112,0.10)" }, svg);
    const t = el("text", { x: pad.l + 4, y: Y(band[1]) + 12, fill: "#009E70", "font-size": 9.5, "font-weight": 700 }, svg);
    t.textContent = "normal range";
  }

  const ticks = 4;
  for (let i = 0; i <= ticks; i++) {
    const v = lo + ((hi - lo) / ticks) * i, y = Y(v);
    el("line", { x1: pad.l, x2: W - pad.r, y1: y, y2: y, stroke: GRID, "stroke-width": 1 }, svg);
    const t = el("text", { x: pad.l - 6, y: y + 3.5, "text-anchor": "end", fill: AXIS, "font-size": 10 }, svg);
    t.textContent = Math.round(v);
  }
  labels.forEach((l, i) => {
    if (i % Math.ceil(labels.length / 7) !== 0 && i !== labels.length - 1) return;
    const t = el("text", { x: X(i), y: H - 8, "text-anchor": "middle", fill: AXIS, "font-size": 10 }, svg);
    t.textContent = l;
  });

  series.forEach(s => {
    const d = s.values.map((v, i) => (i ? "L" : "M") + X(i) + "," + Y(v)).join(" ");
    el("path", { d, fill: "none", stroke: s.color, "stroke-width": 2,
      "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
    // direct label at last point (selective labeling)
    const li = s.values.length - 1;
    el("circle", { cx: X(li), cy: Y(s.values[li]), r: 3.5, fill: s.color,
      stroke: "#0F1117", "stroke-width": 2 }, svg);
  });

  const cross = el("line", { y1: pad.t, y2: pad.t + ih, stroke: "#2A3A50", "stroke-width": 1, opacity: 0 }, svg);
  const dots = series.map(s => el("circle", { r: 4.5, fill: s.color, stroke: "#0F1117", "stroke-width": 2, opacity: 0 }, svg));
  const hit = el("rect", { x: pad.l, y: pad.t, width: iw, height: ih, fill: "transparent" }, svg);
  hit.addEventListener("mousemove", e => {
    const r = box.getBoundingClientRect();
    const scale = W / r.width;
    const mx = (e.clientX - r.left) * scale;
    const i = Math.round(((mx - pad.l) / iw) * (labels.length - 1));
    const ci = Math.max(0, Math.min(labels.length - 1, i));
    cross.setAttribute("x1", X(ci)); cross.setAttribute("x2", X(ci)); cross.setAttribute("opacity", 1);
    let rows = "";
    series.forEach((s, k) => {
      dots[k].setAttribute("cx", X(ci)); dots[k].setAttribute("cy", Y(s.values[ci])); dots[k].setAttribute("opacity", 1);
      rows += `<div class="row"><i class="sw" style="background:${s.color}"></i>${s.name}: <b style="color:#F1F5F9;margin:0">&nbsp;${s.values[ci]}${unit}</b></div>`;
    });
    showTip(tip, box, (e.clientX - r.left), (e.clientY - r.top), `<b>${labels[ci]}</b>${rows}`);
  });
  hit.addEventListener("mouseleave", () => {
    cross.setAttribute("opacity", 0); dots.forEach(d => d.setAttribute("opacity", 0)); tip.style.display = "none";
  });
}
