# Web App (`webapp/`)

The revamped site built July 2026 — replaces the old Netlify landing page. Zero dependencies, fully static, PWA-installable.

## Files

| File | What it is |
|---|---|
| `webapp/index.html` | Marketing site: hero with Telegram-conversation mockup, problem stats, how-it-works, 9-feature grid, comparison table, **pricing (Free / Pro ₹149 / Family ₹249)**, FAQ, disclaimer footer |
| `webapp/app.html` | Interactive dashboard demo (sample data): Home / Food / BP / Sugar tabs, calorie ring, macro bars, 7-day charts, photo-confirm card, BP + glucose trend charts |
| `webapp/css/site.css` | The whole design system — tokens at the top (see [Design System](Design-System.md)) |
| `webapp/js/charts.js` | Dependency-free SVG charts: donut, rounded-top bars with target line, multi-line with normal-range band; hover tooltips; CVD-validated series colors |
| `webapp/manifest.webmanifest` | PWA manifest (installable, dark theme, standalone) |

## Deploy

**Netlify (current host):** drag the `webapp/` folder into Netlify's deploy area, or connect this repo with publish directory `webapp`. No build step.

**Domain:** point `healthsnapindian.com` at the Netlify site (⚠️ DNS currently not resolving — fix first). Keep healthsnapindia.netlify.app as the fallback URL.

## Wiring the demo to live data (v2 task)

`app.html` renders from inline sample arrays (bottom `<script>` block). To go live:

1. Replace the arrays with a fetch from an n8n webhook (or Supabase client query) returning `{days, kcal, protein, bp: {sys, dia}, glucose: {fasting, post}}` for the authenticated user
2. Gate `app.html` behind Supabase auth (phone/Google)
3. The confirm card's buttons should call the n8n callback webhook with `confirm_/edit_/wrong_{{entry_id}}` — same contract as the Telegram inline buttons
4. Keep the chart calls unchanged — `barChart()` / `lineChart()` / `calorieRing()` take plain arrays

## Screens & intent

- **Landing:** convert to "Start free on Telegram" (deep link `t.me/<bot>` — placeholder `https://t.me/` in the HTML must be replaced with the real bot username) and to the demo
- **App demo:** used in sales/marketing to show the dashboard before signup; later becomes the real logged-in PWA
- Comparison table and stats banner carry sourced claims from `business-plan/market-research.md` — keep them in sync if pricing/claims change

## QA checklist (done for this build)

- [x] Rendered and screenshotted at 1280px (landing) and 390px (app) — no layout breaks, no console errors
- [x] Chart palette passes the colorblind/contrast validator on the dark surface
- [x] Charts have hover tooltips + `<details>` data-table fallbacks
- [x] Medical disclaimer + no-auto-charge trial copy present
- [ ] Replace `https://t.me/` placeholders with real bot link before deploy
- [ ] Add real Razorpay checkout links to pricing buttons
