# Business Plan (summary)

Full plan: [`business-plan/README.md`](../business-plan/README.md) · Research with sources: [`business-plan/market-research.md`](../business-plan/market-research.md) · Model: [`business-plan/financial_model.py`](../business-plan/financial_model.py) + [`financial-model.csv`](../business-plan/financial-model.csv)

## Positioning

> For Indian families managing sugar and BP, HealthSnap is the health diary that lives in your Telegram — snap your khaana, send your readings, and see everything your doctor asks for — at ₹149/month, built for Indian food.

**Target segment:** the 40+ "sugar-BP" household — India has **315M hypertensives + 101M diabetics + 136M prediabetics** (ICMR-INDIAB) — plus their adult children as caregivers. Not the gym crowd.

**Three wedges:** ① Telegram-first (zero app fatigue, free Bot API) ② Indian-food accuracy that compounds via the correction loop ③ BP + glucose + diet in one diary (HealthifyMe's answer to this segment is a ₹75,000 CGM bundle).

## Pricing

| Plan | Price | |
|---|---|---|
| Free | ₹0 | 3 photos/day, 7-day history — the hook |
| **Pro** | **₹149/mo** or ₹999/yr | vs HealthifyMe ₹208/mo-effective, MFP ₹540, Cal AI ~₹950 |
| Family | ₹249/mo or ₹1,999/yr | 4 members, caregiver alerts, Pooja voice |

Billing: Razorpay **UPI AutoPay** (UPI = 80%+ of Indian digital payments). 7-day trial, no auto-charge.

## Marketing (the Cal AI playbook, Indianised)

1. **M1–3:** founder network + micro-influencers (diabetes educators, desi-weight-loss creators); chat-link CTA converts with no app-store step
2. **M4–12:** referral engine (give-a-month-get-a-month), creator commission codes, doctor-pad pilot (QR diary pads in clinics), SEO from the food DB ("roti calories")
3. **Y2+:** native Android app, paid ads at proven CAC, family-plan festive campaigns, B2B2C (insurers/diagnostics)

Guardrails: CAC ≤ ₹350 · LTV:CAC ≥ 4:1 · free→paid ≥ 8%.

## Financials (base case)

| Metric | Value |
|---|---|
| Blended gross ARPU | ₹144/mo → net ₹122 ex-GST |
| Variable cost | ₹37/sub/mo (AI ₹15 + free-tier share ₹15 + Razorpay + VAPI) |
| **Contribution margin** | **₹85/mo (70%)** |
| Churn / LTV | 6%/mo → 16.7-mo life → **LTV ₹1,413 → LTV:CAC 4.0:1** |
| EBITDA-positive | **Month 8** |
| Peak funding need | **≈ ₹3.7 lakh** (M17, after ₹2.5L Android build); sustainably cash-positive M24 |
| Year 3 | ~10,000 paying subs · ₹125L gross · ₹14.5L EBITDA |
| Scenarios | Conservative: −₹12L over 3yrs (pause ops ramp) · Ambitious: Y3 ₹2.25Cr gross, ₹44L EBITDA |

**The kill-risk number:** AI vision cost. High-detail GPT-4o = ₹45–90/user/mo (fatal at ₹149). Enforce **low-detail mode + dish caching** (₹15 assumption) in n8n from day 1; cap free tier at 3 photos/day; re-benchmark models quarterly.

**Compliance list (finance owner):** GST registration timing (model assumes M13, under ₹20L Y1 threshold — confirm with CA), TDS on creator payouts, trademark filing, DPDP Act 2023 health-data compliance, medical disclaimer everywhere.
