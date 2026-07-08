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
| **`EMP_BD_LT_15000_AND_NO_PF`** | **your metric — employees below PF ceiling (BASIC+DA < 15,000) with no ECR PF** |
| `EMP_GROSS_LE_21000_AND_NO_ESI` | employees below ESI ceiling (gross ≤ 21,000) but not in ESI |
| `ANOMALY_BELOW_CEILING_native` | same anomaly as flagged by reconcile.py (cross-check) |
| `ROWS_PF_GT_1800` | rows where PF exceeds the ₹1,800 cap |
| `ROWS_ESI_GROSS_GT_21000` | rows in ESI but gross above the ₹21,000 ceiling |
| `ROWS_PF_BDPROJ_GT_15000` | PF rows whose month-projected BASIC+DA exceeds ₹15,000 |
| `ROWS_ESI_075_RELAXED` | rows where the 0.75% ESI rule was relaxed (gross lifted) |
| `ROWS_NEG_OTHER_DED` | rows with negative OTHER_DEDUCTION (should be 0) |
| `EMP_WITH_PF` / `EMP_NO_PF` / `EMP_WITH_ESI` | coverage counts |
| `RULE_PF_ANCHOR` / `RULE_PF_SECONDARY` / `RULE_ESI_ONLY` / `RULE_NO_PF_NO_ESI` | rule-mix row counts |
| `ACTION_NEEDED_ROWS` / `ACTION_NEEDED_EXCESS_SALARY` | April-style action list size + ₹ excess (where an `ACTION_NEEDED_*.csv` exists) |
| `REVISED_PF_TOTAL`, `REVISED_ESIC_TOTAL`, `REVISED_NET_TOTAL` | month ₹ totals |

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
   > one month; each column is a pre-computed count or total. Key columns:
   > `EMP_BD_LT_15000_AND_NO_PF` = employees with BASIC+DA below ₹15,000 and no
   > ECR PF; `EMP_GROSS_LE_21000_AND_NO_ESI` = below ESI ceiling but not in ESI;
   > `ROWS_PF_GT_1800` = PF above the ₹1,800 cap; `ACTION_NEEDED_ROWS` = action
   > list size; `RULE_*` = rule-mix counts; `REVISED_*_TOTAL` = ₹ totals. If the
   > user names a month, filter to that MONTH; if they say 'any month', 'total',
   > or 'whole year', sum the column across all rows. Answer with just the
   > number(s) and the month(s). Amounts are in ₹."
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

## ✅ LIVE STATUS (2026-07-07)

**Working in production.** The deployed workflow is **`n8n_salary_bot_workflow_v2.json`**
("ISPL Salary Query Bot v2") on the user's n8n Cloud, answering via the
**ISPL GST LAW BOT** Telegram bot (its token was repurposed; the old local GST
script is retired). Data source: Google Sheet **`Salary_Exceptions_Summary`**
(ID `1smYxcENYcnfu8rF8uyfuqVUM-Qo_GmuG0-aV6EMA0b8`) in Drive folder
**ISPL SALARY AUDIT 25-26** — 13 months, FY2025-26 (incl. Apr-25 = 455 via
`April2025_Final_Complete.xlsx`) + Apr-26. Year total for the headline anomaly
(BASIC+DA < 15,000 & no ECR PF): **4,679 employees**.

v2 design note: v1 (agent + Sheets *tool*) hallucinated when the tool call
failed. v2 reads the sheet deterministically on every message (Sheets read →
Aggregate → full table embedded in the system prompt, model pinned to gpt-4o).
Use v2 for any future bot of this kind.

## 24/7 operation — the PC is NOT needed for queries

Confirmed setup (2026-07): the user's n8n is **cloud-hosted** (the food-log bot
answers with the PC off). Query path:

    Phone (Telegram) → Telegram servers → n8n Cloud → Google Sheet → reply

The PC and Command Prompt are only needed for **one monthly job**: rebuilding
`Salary_Exceptions_Summary.xlsx` after a new month is reconciled, and
re-uploading it to the Google Sheet. Between refreshes, queries work any time —
PC off, no command prompt.

One n8n rule to remember: a Telegram bot token can only drive **one** active
n8n workflow. Don't reuse the food-bot's token — create a **new bot** with
@BotFather for salary queries (2 minutes, free).

## Two honest limits

- **The bot only answers what's in the summary table.** It's not scanning raw
  rows live. To ask a *brand-new* kind of question (a different condition), add
  that count as a new column in `build_exceptions_summary.py`, rerun, re-upload.
  (Tell me the condition and I'll add the column for you.)
- **Something must run the build step.** The count is computed on your PC from
  the big files; the bot just reads the small result. That's why it's a
  once-a-month double-click, not fully automatic — the source files live on your
  PC, not in the cloud.

## ⏸️ SQL database (Supabase) — paused mid-setup (2026-07-07)

Blocked ONLY by a live Supabase outage ("We are investigating a technical issue"
banner) causing `password authentication failed` on every connect, regardless of
credentials. Our side is confirmed working: the loader reads all **256,276 rows**
across 13 months every run; only the DB login fails during the incident.

**Supabase project (free NANO tier, AWS ap-southeast-1):**
- host: `aws-0-ap-southeast-1.pooler.supabase.com`  · port: `5432` (session pooler)
- user: `postgres.tmjdhakaondusmvcmdmg`  · dbname: `postgres`
- project ref: `tmjdhakaondusmvcmdmg`

**Resume checklist (when the Supabase status banner is gone):**
1. Supabase → Reset database password to a simple alphanumeric value (e.g. `IsplSalary2026`); wait **3 minutes** (no repeated resets — each restarts propagation).
2. In SALARY BOT folder, quick login test:
   `python -c "import psycopg2; psycopg2.connect(host='aws-0-ap-southeast-1.pooler.supabase.com',port=5432,user='postgres.tmjdhakaondusmvcmdmg',password='PW',dbname='postgres'); print('CONNECTED OK')"`
3. On CONNECTED OK, run the loader:
   `python load_to_postgres.py --in "<FY25-26 folder>" "<April-26 folder>" --fy 2025 --host aws-0-ap-southeast-1.pooler.supabase.com --port 5432 --user postgres.tmjdhakaondusmvcmdmg --password PW --dbname postgres`
   → expect `DONE — 256,276 rows now in 'salary_rows'`.
4. Import `n8n_salary_sql_bot.json`, set Postgres (same creds) + OpenAI + Telegram credentials, activate → ask-anything SQL bot live.

### Update (2026-07-08) — 2nd Supabase project, still blocked by the incident
Created a fresh project **ISPLSALARY** (ref `rgfhqghwkiqwhwxjatsc`, region ap-northeast-2)
after the 1st one (created during the outage) kept failing auth. The new one ALSO
returns `password authentication failed` despite a confirmed password — consistent
with the pooler routing for a brand-new project not being active yet while Supabase's
incident is still in "monitoring" (their status page: monitoring for ~1-2 days).

New project pooler details (session): host `aws-1-ap-northeast-2.pooler.supabase.com`,
port `5432`, user `postgres.rgfhqghwkiqwhwxjatsc`, dbname `postgres`.

RESUME: once Supabase status is fully green, either wait ~10 min after project creation
for pooler routing, or spin a fresh project on a healthy day; then run the login test →
loader → import n8n_salary_sql_bot.json (creds = same pooler details + chosen password).
