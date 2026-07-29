# HealthSnap — Business Plan

**Snap your food. Know your health.**
AI food-photo logging built for Indian food, plus BP & sugar tracking — delivered through Telegram and a PWA dashboard.

*Prepared July 2026 · Owner: Dinesh Sharma · All amounts in ₹ unless noted (FX ₹95/$)*

Companion files in this folder:

| File | What it is |
|---|---|
| `market-research.md` | Full competitor / market / cost research with source URLs |
| `financial-model.csv` | 36-month monthly model (base case) — opens in Excel |
| `financial_model.py` | The script that generates every number below (change assumptions, re-run) |
| `../webapp/` | The revamped web app (landing page + dashboard demo) |

---

## 1. Executive summary

HealthSnap lets a user photograph their meal, send it to a Telegram bot, and get the dish identified with calories and macros from a verified Indian food database — confirmed by the user before anything is saved. The same chat logs blood pressure and glucose readings, and a dark-theme PWA dashboard shows trends, estimated HbA1c and a weekly AI summary.

**The one-line pitch:** every photo-calorie app targets young weight-loss users with a US food database and an app they'll stop opening in two weeks. HealthSnap targets India's 315M hypertensives and 101M diabetics (ICMR-INDIAB) with a *sugar-BP-khaana diary that lives inside Telegram* — no app to remember — at ₹149/month when the nearest AI competitor costs ₹208–950/month.

**Headline financials (base case, 36 months):**

| Metric | Value |
|---|---|
| Blended ARPU | ₹144/paying sub/month (gross) |
| Contribution margin | ₹85/sub/month (**70%**) |
| LTV : CAC | **4.0 : 1** (₹1,413 : ₹350) |
| First EBITDA-positive month | **Month 8** |
| Peak funding need | **≈ ₹3.7 lakh** (month 17, after Android build) |
| Year 3 | ~10,000 paying subs · ₹125L gross revenue · ₹14.5L EBITDA |

This is a self-fundable business: total cash at risk is under ₹4 lakh in the base case.

---

## 2. The product

### What exists today
- n8n workflow: Telegram → GPT-4 Vision → Google Sheets (1,183 food logs, 1,012 BP, 1,014 glucose entries of real usage)
- Verified Indian Food Database (999 dishes with Hindi aliases, IFCT-derived nutrition)
- BP + glucose classification flows, dark-theme dashboards, Razorpay test flow, VAPI voice agent ("Pooja")
- Landing page (healthsnapindia.netlify.app; domain healthsnapindian.com — **DNS is currently not resolving, fix before launch**)
- **New (this repo): revamped web app** — `webapp/index.html` (marketing site with pricing) and `webapp/app.html` (interactive PWA dashboard demo), in the brand design language

### Launch-blocking build items (from the commercial architecture already specced)
1. Supabase schema + auth (phone/Google) — multi-user with `user_id` on every record
2. n8n workflow v2: user_id in payloads, Telegram inline confirm buttons, Supabase writes
3. Payment: Razorpay **UPI AutoPay** subscription mandates (UPI is 80%+ of Indian digital payments; cards ~8%)
4. Wire the new webapp to live data (replace sample data in `app.html`)

### Product principles (the moat is in these, not the code)
- **Human-in-the-loop:** nothing saves without user confirm/edit → data users trust, plus a correction stream that continuously improves Indian-dish accuracy
- **Chat-first:** the bot pings the user; 2-tap logging beats app-opening. This is why our own usage data shows month-3 retention where diet apps die
- **Household units:** katori, roti-count, plate — not grams

---

## 3. Market

Full data and sources: `market-research.md`. The load-bearing numbers:

| Fact | Number | Source |
|---|---|---|
| Adults with hypertension in India | **315M (35.5%)** | ICMR-INDIAB-17, Lancet |
| Adults with diabetes / prediabetes | **101M + 136M** | ICMR-INDIAB-17 |
| India fitness app market | $521M (2025) → $2.9B by 2034 | IMARC |
| Health app users in India | 450M+ | Knowledge Sourcing |
| WhatsApp / Telegram India | 536M+ MAU / largest Telegram market globally | Skillademia, WorldPopulationReview |
| Validation of the category | Cal AI: 0 → $30M ARR in ~18 months, acquired by MyFitnessPal (Dec 2025) | TechCrunch, CNBC |

**Target segment (deliberately NOT the gym crowd):** the 40+ "sugar-BP" household — recently diagnosed or borderline diabetics/hypertensives told by a doctor to "track your diet and readings", plus their adult children who manage parents' health remotely. This segment is enormous, underserved by every photo-calorie app, and already asked by doctors to keep exactly the diary HealthSnap produces.

---

## 4. Competition & positioning

| | HealthSnap | HealthifyMe | Cal AI (MFP) | MyFitnessPal | WhatsApp/TG bots |
|---|---|---|---|---|---|
| Indian-food photo AI | ✓ core | ✓ (~75% claimed) | ✗ US-centric | weak on Indian food | ✓ basic |
| BP + glucose + diet in one | **✓ unique** | CGM bundle @ ₹75,000 | ✗ | ✗ | ✗ |
| Chat-native (no app) | **✓** | ✗ | ✗ | ✗ | ✓ |
| Confirm-before-save loop | **✓ unique** | ✗ | ✗ | ✗ | ✗ |
| Effective monthly price | **₹149** | ₹208 (annual-commit) – ₹6,500 | ~₹950 | ~₹540 | free/unproven |
| Scale | pre-launch | 35–40M users, ₹170Cr rev | 15M downloads | 220M registered | ~10K users |

**Positioning statement:**
> *For Indian families managing sugar and BP, HealthSnap is the health diary that lives in your Telegram — snap your khaana, send your readings, and see everything your doctor asks for — at ₹149/month, built for Indian food.*

Three defensible wedges:
1. **Telegram-first, zero app fatigue** — no incumbent can copy this without cannibalising their app engagement metrics; Telegram Bot API is free (vs WhatsApp per-conversation fees), so messaging COGS ≈ 0 while we prove the model.
2. **Indian-food accuracy compounding** — verified DB + every user correction makes the AI better on thalis, where 2026 photo-AI still fails. HealthifyMe is the only real competitor here and they bury Snap inside a ₹2,499/yr bundle.
3. **The metabolic wedge** — BP + glucose + food in one diary for the 40+ segment. HealthifyMe's answer is a ₹75,000 CGM bundle; we do the 80% use-case at 2% of the price.

**What we do NOT do (and say so):** no human coaches (that's HealthifyMe's ₹1,500–6,500/mo game), no gym content, no medical advice.

---

## 5. Marketing plan

**Template: the Cal AI playbook, Indianised** (took Cal AI to $30M ARR bootstrapped — three engines in sequence):

### Phase 1 — Months 1–3: founder-led + micro-influencers (budget ₹5–15k/mo)
- 30–50 seed users from personal/professional network; obsess over their week-2 retention
- Outreach to **micro** health creators (10k–100k followers): diabetes educators, "desi weight loss" creators, yoga/walking-group aunties' favourites — *not* celebrities
- The pitch to creators: a Reel of "I photographed my thali and Telegram told me the calories" — the chat-link CTA converts **without an app-store install step**, which is exactly why bot CAC runs below app-install CAC
- Hindi + English content; WhatsApp-forwardable demo clips

### Phase 2 — Months 4–12: referral engine (budget ₹15–60k/mo, = CAC ₹200 × adds)
- Referral: give a month, get a month (costs ₹126 net ARPU, far below CAC)
- Creator commission codes (20% of first-year revenue of referred subs) — creators become salespeople
- Doctor channel pilot: 10 diabetologists/GPs get a printable "ask your patient to bring this diary" pad with a QR code — the doctor-recommended diary is free distribution into exactly our segment
- SEO/content: "roti calories", "dal chawal calories", "BP 140/90 kya karein" — the food DB itself becomes 1,000 landing pages

### Phase 3 — Year 2+: paid + Play Store (CAC ₹300–350 budgeted)
- Native Android app (85%+ of Indian users; Play Store listing = trust) — ₹2.5L one-time in the model
- Paid Meta/Google ads only after organic funnel metrics are proven (benchmark: health app CAC ₹400–520; we budget ₹300–350 with chat-link advantage)
- Family-plan push around parents' health ("track mummy-papa's BP from Bangalore") — Raksha Bandhan / Diwali campaigns
- Corporate/insurer wellness pilots as a Year-3 B2B2C channel

**KPI guardrails:** CAC ≤ ₹350 · LTV:CAC ≥ 4:1 · month-1 paying retention ≥ 85% · weekly log rate ≥ 4 days/user · free→paid conversion ≥ 8–12%

---

## 6. Pricing

| Plan | Price | Notes |
|---|---|---|
| Free | ₹0 | 3 photo logs/day, BP+sugar logging, 7-day history — the hook |
| **Pro** | **₹149/mo** or ₹999/yr (–44%) | unlimited logs, full history, HbA1c, AI summary, PDF export |
| Family | ₹249/mo or ₹1,999/yr | Pro × 4 members, caregiver alerts, Pooja voice |

- Sits below every AI competitor (HealthifyMe Smart ₹208/mo-effective annual-commit, MFP ₹540, Cal AI ~₹950) and below OpenAI's India price anchor (ChatGPT Go ₹399)
- **7-day trial, no auto-charge without consent** — trust matters in this segment
- Billing via Razorpay UPI AutoPay (fees 2% + GST modeled); annual plans pushed hard because they neutralise the 8–15% UPI mandate-failure churn
- Assumed paying mix: 60% Pro monthly / 25% Pro annual / 15% Family → **blended gross ARPU ₹144/month**

---

## 7. Financial plan

Every number generated by `financial_model.py`; monthly detail in `financial-model.csv`. Consumer prices are GST-inclusive; output GST (18%) applied from month 13 (Year-1 gross ≈ ₹8L stays under the ₹20L service registration threshold — **confirm with CA**, register earlier if inter-state supply rules require).

### 7.1 Cost structure

**One-time (pre-launch, ≈ ₹1.0–1.5L):** Supabase+auth build, n8n v2 workflow, webapp wiring, food-DB verification push, legal (T&C/privacy), trademark filing. Year-2 one-time: native Android app ₹2.5L.

**Fixed monthly (Year 1 ≈ ₹11k):** n8n Cloud Pro $60 · Supabase Pro $25 · Netlify $20 · domain/email/tools ~$10. Scales to ₹22k (Y2) and ₹40k (Y3) with volume tiers.

**Variable per paying subscriber per month (₹37 total):**

| Item | ₹/sub/mo | Basis |
|---|---|---|
| AI vision — paying user | 15 | ~90 photos × ₹0.17 (GPT-4o low-detail ≈ 85 img tokens + prompt ≈ $0.002/photo) with dish-cache |
| AI vision — free-tier share | 15 | 6 free users per paying sub × ₹2.5 (capped 3/day, actual ~10–15 photos/mo) |
| Razorpay | 3.4 | 2% + 18% GST on fee, on ₹144 ARPU |
| VAPI voice (Family only) | 3.75 | ₹25 × 15% family mix |

**People & ops:** ₹15k/mo Y1 (part-time support VA + content) → ₹60k/mo Y2 → ₹150k/mo Y3 (support + dietitian for DB verification + growth exec). Founder salary excluded (side-project phase); add when funded.

**Marketing:** budgeted as CAC × gross adds — ₹200 (Y1, organic-heavy) / ₹300 (Y2) / ₹350 (Y3).

### 7.2 Unit economics

| Metric | Value |
|---|---|
| Gross ARPU | ₹144 /mo |
| Net ARPU (ex-GST) | ₹122 /mo |
| Variable cost | ₹37 /mo |
| **Contribution margin** | **₹85 /mo (70%)** |
| Monthly churn (incl. UPI mandate failures) | 6% → 16.7-month avg life |
| **LTV** | **₹1,413** |
| **LTV : CAC (₹350)** | **4.0 : 1** ✅ (benchmark 4–5:1) |

> ⚠️ **The one number that can kill this business:** AI vision cost. At high-detail GPT-4o a heavy user costs ₹45–90/mo — untenable at ₹149. The model assumes low-detail mode + caching of common dishes (₹15/mo). Enforce this in the n8n workflow from day 1, cap free tier at 3 photos/day, and re-benchmark cheaper models quarterly.

### 7.3 Year-1 monthly P&L (base case, ₹)

| Month | Adds | Paying subs | Free users | Gross revenue | AI cost | Marketing | Total EBITDA |
|---|---|---|---|---|---|---|---|
| M1 | 25 | 25 | 150 | 3,596 | 750 | 5,000 | −28,332 |
| M2 | 40 | 64 | 381 | 9,135 | 1,905 | 8,000 | −27,224 |
| M3 | 55 | 115 | 688 | 16,499 | 3,441 | 11,000 | −24,762 |
| M4 | 60 | 168 | 1,007 | 24,140 | 5,034 | 12,000 | −20,093 |
| M5 | 82 | 240 | 1,438 | 34,488 | 7,192 | 16,400 | −16,818 |
| M6 | 104 | 329 | 1,976 | 47,379 | 9,881 | 20,800 | −11,655 |
| M7 | 126 | 436 | 2,614 | 62,662 | 13,068 | 25,200 | −4,718 |
| **M8** | 148 | 557 | 3,345 | 80,193 | 16,724 | 29,600 | **+3,886** |
| M9 | 170 | 694 | 4,164 | 99,836 | 20,820 | 34,000 | +14,057 |
| M10 | 192 | 844 | 5,066 | 121,466 | 25,331 | 38,400 | +25,702 |
| M11 | 214 | 1,008 | 6,046 | 144,963 | 30,231 | 42,800 | +38,731 |
| M12 | 236 | 1,183 | 7,099 | 170,214 | 35,497 | 47,200 | +53,063 |

(Also in each month: infra ₹11k, people ₹15k, Razorpay ~2.4%, VAPI. Full columns in the CSV.)

### 7.4 Three-year P&L — three scenarios (₹ lakh)

**BASE** (1,183 → 4,467 → 9,990 paying subs at year-ends):

| Line | Y1 | Y2 | Y3 |
|---|---|---|---|
| Gross revenue | 8.1 | 48.3 | 125.1 |
| Less output GST | 0.0 | 7.4 | 19.1 |
| Net revenue | 8.1 | 40.9 | 106.0 |
| AI / vision | 1.7 | 10.1 | 26.1 |
| Payment fees | 0.2 | 1.1 | 3.0 |
| Voice (VAPI) | 0.2 | 1.3 | 3.3 |
| Infrastructure | 1.3 | 2.6 | 4.8 |
| Marketing | 2.9 | 15.3 | 36.4 |
| People & ops | 1.8 | 7.2 | 18.0 |
| One-time (Android app) | — | 2.5 | — |
| **EBITDA** | **0.0** | **+0.8** | **+14.5** |

**CONSERVATIVE** (half the base growth): 592 → 2,233 → 4,995 subs; EBITDA −1.6 / −5.8 / −4.2. Still only ~₹12L total cash burn over 3 years — survivable as a side project; the fix is pausing the Y2/Y3 people ramp until growth justifies it.

**AMBITIOUS** (1.8× base, Cal-AI-style creator flywheel catches): 2,130 → 8,040 → 17,983 subs; EBITDA +2.5 / +11.3 / **+44.3**; Y3 gross revenue ₹2.25 crore.

### 7.5 Cash & funding

- **First EBITDA-positive month: M8.** Cash dips again at M13 (₹2.5L Android build + GST + ops step-up)
- **Peak cumulative funding need: ≈ ₹3.7 lakh at M17**; cumulative cash sustainably positive from **M24**; cumulative +₹15.3L by M36
- Recommendation: earmark **₹5 lakh** of personal capital as the full 3-year war chest (base case); no external funding required. Raise only if the ambitious path materialises and you want to buy growth faster
- **Compliance checklist (finance owner's list):** GST registration timing & place-of-supply for OIDAR-like services (confirm with CA), 18% GST invoicing via Razorpay, TDS on creator payouts (194C/194J), trademark "HealthSnap" (Class 9/42/44), privacy policy + DPDP Act 2023 compliance for health data, standard medical disclaimer everywhere (already on the new site)

### 7.6 Sensitivity (what to watch monthly)

| Lever | Base | Danger line | Effect |
|---|---|---|---|
| AI cost/paying sub | ₹15 | > ₹40 | CM drops 70% → 49%; LTV:CAC < 3 |
| Monthly churn | 6% | > 10% | LTV ₹1,413 → ₹850; marketing stalls growth |
| CAC | ₹300–350 | > ₹500 | payback > 6 months; cut paid, back to referral |
| Free:paid ratio | 6:1 | > 12:1 | free-tier AI cost doubles; tighten photo cap |
| Conversion free→paid | 8–12% | < 5% | funnel leak — fix trial nudges before spending on traffic |

---

## 8. Roadmap

| When | Milestone |
|---|---|
| M0 (now) | Fix healthsnapindian.com DNS → point to new webapp; deploy `webapp/` to Netlify |
| M1 | Supabase + auth + n8n v2 (confirm loop, user_id); Razorpay UPI AutoPay; 30 seed users |
| M2–M3 | First 10 micro-influencer collabs; referral codes; iterate on week-2 retention |
| M4–M6 | Doctor-pad pilot (10 clinics); 300+ paying subs; food DB → 1,500 dishes |
| M7–M12 | Scale creator engine; ~1,200 paying subs; EBITDA positive (M8) |
| M13–M18 | Native Android app; GST registration; Family-plan festive campaigns |
| M19–M36 | Paid acquisition at proven CAC; B2B2C pilots (insurers/diagnostics); 10k subs |

---

## 9. Risks & mitigations

1. **AI cost blowout** — enforce low-detail + caching from day 1; photo caps on free; quarterly model re-benchmark (biggest financial risk, see §7.6)
2. **Accuracy disappointment** → the confirm-loop is the mitigation: users correct, we learn, and trust survives because nothing saves unverified
3. **HealthifyMe copies chat-first** → they're structurally disincentivised (app engagement is their business); our speed + niche focus + price is the answer, and an acquisition by them is an acceptable outcome (MFP just bought Cal AI)
4. **UPI AutoPay churn (8–15% mandate failures)** → push annual plans (25%+ of mix), pre-expiry Telegram nudges, one-tap re-subscribe
5. **Health-data regulation (DPDP Act)** → consent-first onboarding, export/delete self-serve, data minimisation; never sell data
6. **Telegram platform risk** → the architecture (n8n + Supabase) is channel-agnostic; WhatsApp Business API is the ready fallback (paid, but proven by WhatFit)
7. **Founder bandwidth (side project)** → M4+ support VA; automation-first ops (n8n is already the ops layer)
