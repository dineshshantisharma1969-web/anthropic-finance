# Design System

Dark theme always. Vibrant color-coded metrics — never grey everything. Mobile-first. Indian food examples as defaults. Telegram status shown prominently (it's the commercial differentiator).

## Brand palette (UI accents — buttons, chips, status, text highlights)

| Token | Hex | Use |
|---|---|---|
| Background | `#0F1117` | Page background, always |
| Card | `#161B27` · alt `#1A2235` | Surfaces |
| Border | `#1E2A3A` · strong `#2A3A50` | Hairlines |
| **Primary green** | `#00E5A0` | Food / confirm / CTAs (text on it: `#04110C`) |
| Coral red | `#FF6B6B` | BP / alerts |
| Amber | `#FFD93D` | Glucose / "AI estimated" |
| Purple | `#A78BFA` | Weight / protein |
| Blue | `#60A5FA` | Corrected entries / info |
| Orange | `#FF9F43` | Pending |
| Text | `#F1F5F9` / `#94A3B8` / `#64748B` | primary / secondary / muted |

## Chart series palette (marks only — validated)

The neon brand colors are **too light for chart marks** on the dark surface (they sit outside the OKLCH L 0.48–0.67 band, and blue↔purple is indistinguishable under deuteranopia, ΔE 0.3). Chart marks use darker steps of the same hues, which **pass all colorblind + contrast checks** on `#0F1117`:

| Series token | Hex | Assigned to |
|---|---|---|
| `--ch-green` | `#009E70` | Calories / primary series |
| `--ch-amber` | `#BD8600` | Glucose fasting / carbs |
| `--ch-purple` | `#7A5CEE` | Protein / diastolic / post-meal |
| `--ch-coral` | `#D63E4C` | Systolic / fat / target lines |

Rules: never place blue+purple adjacent in a chart; ≤4 series then fold to "Other"; text/labels always wear text tokens, never series colors; every multi-series chart gets a legend + a data-table fallback; sequential data = one hue light→dark, never a rainbow.

## Chart anatomy (implemented in `webapp/js/charts.js`)

- 2px lines, rounded caps; bars ≤34px wide with 4px rounded tops anchored to the baseline
- Recessive grid (`#1E2A3A`), axis text `#64748B` at 10px
- Normal-range bands as 10%-opacity green fills with a small in-band label
- Hover: crosshair + tooltip (hit targets bigger than marks); direct label only on the latest point
- Target lines: dashed 2px coral with right-aligned label

## Status color coding (entries)

🟢 Confirmed → green · 🔵 Corrected → blue · 🟡 AI estimated → amber · 🟠 Pending → orange (chips styled as `--green-dim` etc. 12%-opacity fills with 25%-opacity borders)

## Components (see `webapp/css/site.css`)

- **Buttons:** pill (999px radius), `.btn-primary` green with near-black text, `.btn-ghost` bordered; full-width on mobile
- **Cards:** 16px radius, 1px border, 22px padding
- **Chips:** pill badges with dot indicators (Telegram status, trust strip)
- **Phone mockup:** pure-CSS Telegram conversation (no images) — reuse for campaigns
- **App shell:** 460px max-width, sticky top bar, bottom tab bar with safe-area inset, floating 📸 FAB
- **Typography:** system font stack; headings 800–850 weight with −0.02em tracking; hero `clamp(34px, 5vw, 54px)`

## Voice & tone

- Hinglish-friendly ("khaana", "mummy-papa", "Namaste 🙏") without being cartoonish
- Numbers in Indian format (₹, Cr/lakh, `toLocaleString("en-IN")`)
- Always present: medical disclaimer; "you confirm before anything is saved" trust language
- Honest comparisons — name competitors' strengths, cite indicative prices

## Design iteration backlog

Design feedback rounds are expected (owner has detailed input pending). Capture each round here:

| Date | Feedback | Change | Status |
|---|---|---|---|
| — | *(pending owner's design notes)* | | |
