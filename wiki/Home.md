# HealthSnap Wiki

**Snap your food. Know your health.** — AI food-photo logging built for Indian food, plus BP & glucose tracking, delivered through a Telegram bot and a PWA dashboard.

> Owner: Dinesh Sharma (dinesh@impressionsgroup.in) · Custom domain: healthsnapindian.com · Current landing: healthsnapindia.netlify.app · n8n: kappulearnn8n.app.n8n.cloud

## How it works (30 seconds)

1. 📸 User sends a food photo (or text like "2 roti aloo sabzi") to the **Telegram bot**
2. 🤖 **n8n** routes it to **GPT-4 Vision**, which identifies the dish against the verified **Indian Food Database**
3. ✅ User **confirms / edits** the result (nothing is saved unverified)
4. 📊 The entry lands in the **Food Intake Tracker** (Google Sheets today → Supabase in v2) and appears on the dashboard
5. ❤️ The same chat logs **BP readings** ("122/79") and **glucose** ("sugar 96 fasting")

## Pages

| Page | What's in it |
|---|---|
| [Architecture](Architecture.md) | System diagram, components, data flow, v1 → v2 (multi-user) plan |
| [Workflows](Workflows.md) | n8n workflow inventory, the confirmation loop, meal-timing fix, bot commands |
| [Food Intake Tracker](Food-Intake-Tracker.md) | The Google Sheet: every tab, columns, formulas, dashboards, known fixes |
| [Food Database](Food-Database.md) | Dish schema, categories, Hindi aliases, verification rules, expansion plan |
| [Web App](Web-App.md) | The revamped site + PWA dashboard demo (`webapp/`), how to deploy |
| [Design System](Design-System.md) | Brand colors, validated chart palette, UI components, design principles |
| [Business Plan](Business-Plan.md) | Positioning, pricing, marketing, 3-year financials (summary + links) |

## Current status (July 2026)

| Area | State |
|---|---|
| Telegram → GPT-4 Vision → Sheets flow | ✅ Working (v1), single-user |
| Real usage data | 1,183 food logs · 1,012 BP · 1,014 glucose entries |
| Food Database | 999 dishes with Hindi aliases (subset human-verified) |
| Web app | ✅ Revamped (`webapp/`), sample data, ready to deploy |
| Business plan | ✅ Complete (`business-plan/`) |
| Custom domain DNS | ⚠️ healthsnapindian.com not resolving — fix before launch |
| Multi-user (Supabase + auth) | 🔜 Next build (see [Architecture](Architecture.md)) |
| Payments (Razorpay UPI AutoPay) | 🔜 Next build |
