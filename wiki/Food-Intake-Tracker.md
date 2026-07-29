# Food Intake Tracker (Google Sheet)

The single Google Sheets file behind v1: **`Food_Intake_Tracker`** (Drive, owner dinesh@impressionsgroup.in). It holds the food database, all logs, and the generated dashboards. In v2 it becomes admin-only; Supabase takes over user data.

## Tabs

| Tab | Rows (Jul 2026) | Type | Purpose |
|---|---|---|---|
| Food Database | 999 | Reference | Verified Indian dishes — see [Food Database](Food-Database.md) |
| Food Log | 1,183 | Data entry | Raw entries appended by n8n from Telegram |
| BP Log | 1,012 | Data entry | Blood-pressure readings |
| Sugar Log | 1,014 | Data entry | Glucose readings |
| Food Dashboard | generated | Data dashboard | Today vs targets, meal breakdown, 7/30-day tables (no charts) |
| Food Visuals | generated | Charts | Calorie trend, meal pie, macro stacked bars |
| Health Dashboard | generated | Data dashboard | Latest BP/glucose + 14-day summaries |
| Health Visuals | generated | Charts | BP + glucose trend charts |

## Column schemas

**Food Log** (appended by n8n `Log Food Entry`):

| Col | Field | Notes |
|---|---|---|
| A | Timestamp | full datetime |
| B | Date | used by every SUMIF |
| C | Food Items | free text, e.g. "2 Rotis, Mutton Curry, Paneer Tikka…" |
| D | Meal Type | formula/expression driven — see fixes below |
| E–J | Calories, Protein (g), Carbs (g), Fat (g), Fiber (g), Sugar (g) | numeric |
| K | Health Rating (1–10) | AI-assigned |
| L | Suggestions | AI text |
| M | chat_id | Telegram chat (e.g. 688852870) — multi-user seed |
| N | bot_message_id | lets the bot edit/correct a specific logged message |

**BP Log:** Timestamp · Date · Time · Systolic · Diastolic · Pulse · Category (Normal/Elevated/Stage 1/Stage 2) · Device

**Sugar Log:** Timestamp · Date · Time · Glucose (mg/dL) · Reading Type (Fasting/Post-meal/Random) · Category · Device

## Daily targets (drive all status formulas)

| Metric | Target | | Metric | Target |
|---|---|---|---|---|
| Calories | 2,000 kcal | | Fiber | 25 g |
| Protein | 60 g | | Sugar | ≤ 50 g |
| Carbs | 250 g | | BP | < 120/80 |
| Fat | 65 g | | Fasting glucose | 70–100 mg/dL · Pulse 60–100 |

## Key formulas

```text
Today calories:      =IFERROR(SUMIF('Food Log'!B:B,TODAY(),'Food Log'!E:E),0)
Today by meal:       =IFERROR(SUMIFS('Food Log'!E:E,'Food Log'!B:B,TODAY(),'Food Log'!D:D,"Lunch"),0)
Meal count today:    =COUNTIF('Food Log'!B:B,TODAY())
Latest BP:           =IFERROR(INDEX('BP Log'!D:D,MATCH(MAX('BP Log'!A:A),'BP Log'!A:A,0)),"No Data")
14-day avg systolic: =IFERROR(ROUND(AVERAGEIF('BP Log'!B:B,">="&(TODAY()-14),'BP Log'!D:D),1),0)
Calorie status:      =IF(B3-C3>200,"Under Target",IF(C3-B3>200,"Over Target","On Track"))
```

## Known issue: Column D (Meal Type) breaks on new rows

Row-by-row formulas don't extend when n8n appends. **Permanent fix — one ArrayFormula in D1, delete everything else in column D:**

```text
=ArrayFormula(IF(ROW(A:A)=1,"Meal Type",IF(A2:A="","",
 IF(HOUR(A2:A)<11,"Breakfast",
 IF(HOUR(A2:A)<13,"Snack",
 IF(HOUR(A2:A)<16,"Lunch",
 IF(HOUR(A2:A)<20,"Evening Snack","Dinner")))))))
```

Sheet meal windows (Dinesh's original logic): <11:00 Breakfast · 11–12:59 Snack · 13–15:59 Lunch · 16–19:59 Evening Snack · 20:00+ Dinner.

> ⚠️ The n8n bot uses a different window table (see [Workflows](Workflows.md)). Reconcile to one canonical table before v2 — otherwise the bot's "Logged under Lunch" and the sheet's Column D can disagree for 11:00–15:59 entries.

## Dashboards (Apps Script)

- Run via **Extensions → Apps Script → `buildDashboard()`** — rebuilds all 4 dashboard sheets (deletes + recreates them; raw logs untouched)
- Full script is preserved in the `HEALTHSNAP_SKILL` Google Doc on Drive; colors follow the [Design System](Design-System.md) (`#0F1117` background etc.)
- Paste **only** the JavaScript; any trailing plain-text line causes a SyntaxError. Script must end with `// END OF SCRIPT`
- Sections: Food Dashboard (today's 6 metrics vs targets with 🟢🟡🔴 status, meal breakdown, 7-day + 30-day tables) · Health Dashboard (latest BP/glucose/pulse + 14-day summaries) · Visuals sheets (30-day calorie line vs target, meal-type pie, 7-day macro stacked bars, BP/glucose trend lines)

## Related customer sheets (commercial pilot)

| Drive file | Purpose |
|---|---|
| `HealthSnap_Master_Customers` | One row per customer: profile, conditions, plan (Trial/Pro), Razorpay payment id, link to personal sheet, AI health summary |
| `HealthSnap_Customer_Sheets/` folder | Per-customer sheet (Food Log / BP Log / Sugar Log / AI Health Summary tabs) — the v1 "multi-user" stopgap |
| `HealthSnap_Pro_Form_Responses` | Onboarding Google Form responses (name, mobile/Telegram, DOB, conditions, goal, plan) |

These prove the onboarding→payment→personal-sheet flow but don't scale — v2 replaces them with Supabase (see [Architecture](Architecture.md)).
