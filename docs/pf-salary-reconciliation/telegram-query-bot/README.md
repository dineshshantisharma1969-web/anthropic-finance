# 💬 Ask your salary data from Telegram (mobile)

Goal: text a Telegram bot a question like
**"How many employees had BASIC+DA below 15,000 but ECR PF = 0 in April?"**
and get the number back on your phone.

You already have the whole tech stack for this — your **n8n** instance runs a
Telegram bot today (the food-log bot, workflow `K8jzjNw9YdkrMMn6`, Telegram →
AI Agent → Google Sheets). We reuse that exact pattern, just pointed at salary
data instead of the food log.

---

## The key idea (read this first)

Your reconciled files are **18–20 MB, ~21,000 rows each**. A chat bot **cannot**
scan those on every message — it would time out. So we don't let the bot read
the big files. Instead:

1. **Once per month** (on your PC) we boil the big files down to a **tiny
   summary table** — one row per month, ~10 columns — using the included
   `build_exceptions_summary.py` script.
2. That tiny table goes into a **Google Sheet**.
3. The **Telegram bot reads the small Google Sheet** and answers instantly.

Your specific question (`BASIC+DA < 15,000` **and** `ECR_PF = 0`) is already a
column in that summary: **`EMP_BD_LT_15000_AND_NO_PF`**. It's the same metric
`reconcile.py` calls `ANOMALY_BELOW_CEILING`.

---

## Part 1 — Build the summary table (one-time + repeat each new month)

1. Put `build_exceptions_summary.py` and `build_summary.bat` (both in this
   folder) somewhere on your PC.
2. Open `build_summary.bat` in Notepad and check the two `--in` paths point at
   your real folders (they're pre-filled with your known folders):
   - FY2025-26: `...\ESI_WASHING_REALLOCATED`
   - April-26:  `D:\Desktop Data\21062026\desktop salary folder`
3. **Double-click `build_summary.bat`.** It reads every `*_Final_Complete.xlsx`
   it finds and writes **`Salary_Exceptions_Summary.xlsx`** (tiny).
   - It also prints the grand total to the screen, e.g.
     `TOTAL employees BASIC+DA<15000 with no ECR PF across all months = ...`

> That printed total already answers your question — even before any bot.

### What the summary contains (one row per month)
| Column | Meaning |
|---|---|
| `MONTH` | e.g. 2026-04 |
| `TOTAL_EMPLOYEES` | employees that month |
| **`EMP_BD_LT_15000_AND_NO_PF`** | **your metric — count below PF ceiling with no ECR PF** |
| `ANOMALY_BELOW_CEILING_native` | the same count as flagged by reconcile.py (cross-check) |
| `EMP_WITH_PF` / `EMP_NO_PF` | PF-covered vs not |
| `REVISED_PF_TOTAL`, `REVISED_ESIC_TOTAL`, `REVISED_NET_TOTAL` | month totals |

---

## Part 2 — Put the summary in Google Drive as a Sheet

1. Upload `Salary_Exceptions_Summary.xlsx` to your Google Drive
   (dinesh@impressionsgroup.in).
2. Right-click it → **Open with → Google Sheets** → **File → Save as Google
   Sheets** (so the bot can read it live).
3. Note the sheet name (e.g. `Salary_Exceptions_Summary`).

---

## Part 3 — Wire the Telegram bot in n8n (reuses your food-bot pattern)

Create a **new workflow** (don't touch the food-log one) with these nodes:

1. **Telegram Trigger** — new bot from @BotFather, or a second command on your
   existing bot. This is what you message from your phone.
2. **AI Agent** (OpenAI, same credential you already use) with a **Google Sheets
   "Read Rows" tool** attached, pointed at the `Salary_Exceptions_Summary`
   sheet. System prompt, roughly:
   > "You answer questions about monthly salary/PF/ESI reconciliation. Use the
   > Google Sheets tool to read the Salary_Exceptions_Summary sheet. Each row is
   > one month. The column `EMP_BD_LT_15000_AND_NO_PF` = employees with BASIC+DA
   > below ₹15,000 and no ECR PF. If the user names a month, filter to that
   > MONTH; if they say 'any month' or 'total', sum the column across all rows.
   > Answer with just the number and the month(s). Amounts are in ₹."
3. **Telegram → Send Message** — reply text = `{{ $json.output }}` (same as your
   food bot's `Send Summary` node).

Connect: **Telegram Trigger → AI Agent → Send Message.** Activate the workflow.

Now from your phone: *"employees below 15000 with no PF in April?"* →
the bot reads the sheet → replies with the count. Ask *"...for the whole year?"*
and it sums every month.

---

## Keeping it current

Every time you reconcile a **new month**, just double-click `build_summary.bat`
again — it re-reads all `*_Final_Complete.xlsx` files and rebuilds the summary.
Re-upload it to the same Google Sheet (or use Drive's "Manage versions" /
overwrite) and the bot instantly answers about the new month too. No bot changes
needed.

---

## Two honest limits

- **The bot only answers what's in the summary table.** It's not scanning raw
  rows live. To ask a *brand-new* kind of question (a different condition), add
  that count as a new column in `build_exceptions_summary.py`, rerun, re-upload.
  (Tell me the condition and I'll add the column for you.)
- **Something must run the build step.** The count is computed on your PC from
  the big files; the bot just reads the small result. That's why it's a
  once-a-month double-click, not fully automatic — the source files live on your
  PC, not in the cloud.
