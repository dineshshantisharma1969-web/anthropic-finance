# Fix: Food log entries always categorised as "Lunch"

## Affected workflow
- **Name:** Food Agent - Photo Flow (v1)
- **n8n workflow ID:** `K8jzjNw9YdkrMMn6`
- **Node:** `Log Food Entry` (Google Sheets → append to "Food Log" sheet)

## Problem
The `Meal Type` column was populated by the AI agent via:

```
={{ /*n8n-auto-generated-fromAI-override*/ $fromAI('Meal_Type', ``, 'string') }}
```

The agent's system prompt contained no rule for choosing breakfast/lunch/dinner and
received no time-of-day context, so the model defaulted almost every entry to "Lunch".

## Fix
Make the meal type deterministic from the time the entry is logged (IST). Replace the
`Meal Type` field value in the `Log Food Entry` node with:

```
={{ ({0:"Dinner",1:"Dinner",2:"Dinner",3:"Dinner",4:"Breakfast",5:"Breakfast",6:"Breakfast",7:"Breakfast",8:"Breakfast",9:"Breakfast",10:"Breakfast",11:"Lunch",12:"Lunch",13:"Lunch",14:"Lunch",15:"Lunch",16:"Snack",17:"Snack",18:"Snack",19:"Dinner",20:"Dinner",21:"Dinner",22:"Dinner",23:"Dinner"})[$now.setZone("Asia/Kolkata").hour] }}
```

`setZone("Asia/Kolkata")` ensures correct bucketing even if the n8n server runs in UTC.

## Meal time windows (IST)
| Time (IST)      | Meal      |
|-----------------|-----------|
| 04:00 – 10:59   | Breakfast |
| 11:00 – 15:59   | Lunch     |
| 16:00 – 18:59   | Snack     |
| 19:00 – 03:59   | Dinner    |

## Show the meal in the Telegram confirmation
To make the bot's reply state which meal it logged, edit the `Send Summary` node's
`Text` field (currently `={{ $json.output }}`) to:

```
={{ $json.output }}

🍽️ Logged under: {{ ({0:"Dinner",1:"Dinner",2:"Dinner",3:"Dinner",4:"Breakfast",5:"Breakfast",6:"Breakfast",7:"Breakfast",8:"Breakfast",9:"Breakfast",10:"Breakfast",11:"Lunch",12:"Lunch",13:"Lunch",14:"Lunch",15:"Lunch",16:"Snack",17:"Snack",18:"Snack",19:"Dinner",20:"Dinner",21:"Dinner",22:"Dinner",23:"Dinner"})[$now.setZone("Asia/Kolkata").hour] }}
```

It reuses the same time expression and runs in the same execution as `Log Food Entry`,
so the label shown always matches the `Meal Type` written to the sheet.

## Notes
- Both changes are single-field UI edits rather than a programmatic workflow rewrite,
  to avoid unbinding the live Telegram / OpenAI / Google Sheets credentials.
- To adjust the windows later, change which hour keys (0–23) map to which meal label
  in BOTH expressions so the sheet and the Telegram message stay in sync.
