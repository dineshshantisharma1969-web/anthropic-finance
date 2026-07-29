# n8n Workflows

Instance: **kappulearnn8n.app.n8n.cloud** · Shared error handler emails dinesh@impressionsgroup.in on any failure (workflow "ISPL Error Alerts (email)" pattern).

## HealthSnap workflow inventory

| Workflow | n8n ID | Status | Purpose |
|---|---|---|---|
| **Food Agent - Photo Flow (v1)** | `K8jzjNw9YdkrMMn6` | Main food flow (currently inactive — reactivate for launch) | Telegram photo/text → GPT-4 Vision → `Log Food Entry` (Sheets append) → `Send Summary` reply |
| AttendanceSnap v2 - AI Agent with Memory | `PxA7XLCW7uStG8cs` | ✅ Active | Attendance check-in/out via Telegram (separate product) |
| Health Tracker - Food BP Sugar | `KhkxH9LINyOT8Zsf` (+ older copies) | Legacy | Earlier combined tracker iterations — keep as reference, don't extend |

> Several near-duplicate "Health Tracker - Food BP Sugar" and "AttendanceSnap" copies exist from iteration. Treat the IDs above as canonical; archive the rest to avoid editing the wrong one.

## Food Agent — Photo Flow (v1) node map

```
Telegram Trigger → Get Photo → GPT-4 Vision (AI Agent) → Log Food Entry (Sheets append) → Send Summary (Telegram)
```

Key node fields:

- **Log Food Entry** appends to `Food Log` tab with columns A–N (see [Food Intake Tracker](Food-Intake-Tracker.md))
- `Meal Type` is set **deterministically from IST time**, not by the AI (fix below)
- `chat_id` + `bot_message_id` are stored per row — this is what makes edits/corrections addressable

## The meal-timing fix (docs/food-log-meal-timing-fix.md)

**Problem:** `Meal Type` used `$fromAI('Meal_Type', ...)` with no time context — the model defaulted almost everything to "Lunch".

**Fix:** replace the field with an hour-map expression pinned to IST:

```js
={{ ({0:"Dinner",1:"Dinner",2:"Dinner",3:"Dinner",4:"Breakfast",5:"Breakfast",
6:"Breakfast",7:"Breakfast",8:"Breakfast",9:"Breakfast",10:"Breakfast",
11:"Lunch",12:"Lunch",13:"Lunch",14:"Lunch",15:"Lunch",
16:"Snack",17:"Snack",18:"Snack",
19:"Dinner",20:"Dinner",21:"Dinner",22:"Dinner",23:"Dinner"})
[$now.setZone("Asia/Kolkata").hour] }}
```

| Time (IST) | Meal |
|---|---|
| 04:00 – 10:59 | Breakfast |
| 11:00 – 15:59 | Lunch |
| 16:00 – 18:59 | Snack |
| 19:00 – 03:59 | Dinner |

The same expression is appended to the `Send Summary` text ("🍽️ Logged under: …") so the Telegram reply always matches the sheet. Both are single-field UI edits — do **not** re-import the workflow programmatically, it would unbind the live Telegram/OpenAI/Sheets credentials.

> Note: the Google Sheet's own Column-D formula uses a slightly different window set (11:00–12:59 = Snack, 13:00–15:59 = Lunch — Dinesh's original logic). **Pick one canonical window table before v2** so bot, sheet and dashboard never disagree.

## Telegram inline confirm buttons (v2 spec)

```json
{
  "text": "📱 Detected: Dal Chawal\n🔥 Calories: 520 kcal\n\nIs this correct?",
  "reply_markup": { "inline_keyboard": [[
    {"text": "✅ Yes, save it", "callback_data": "confirm_{{entry_id}}"},
    {"text": "✏️ Edit",        "callback_data": "edit_{{entry_id}}"},
    {"text": "❌ Wrong dish",  "callback_data": "wrong_{{entry_id}}"}
  ]]}
}
```

## Bot commands (user-facing)

| Command / message | Result |
|---|---|
| *(photo of food)* | Detect → confirm → log |
| `log food today` | Manual food log entry |
| `food summary today` / `calories this week` | Summaries from the tracker |
| `122/79` (or `BP 122 79 pulse 74`) | BP logged + classified (Normal → Stage 2), alert if Stage 2+ |
| `sugar 96 fasting` / `sugar 134 after lunch` | Glucose logged + classified; feeds estimated HbA1c (90-day avg) |
| `BP today` / `BP trend 30 days` / `glucose today` / `estimated HbA1c` | Readbacks |

## Debugging a failing workflow

1. n8n → Executions → filter failed → open last failed run
2. Identify failing node + error message (error-alert email contains workflow name, node, message, execution link)
3. Common causes: Telegram file download timeout, OpenAI rate limit, Sheets append quota, expired credentials
4. Fix in the node UI (preserve credentials); re-run the failed execution to verify
