# 📱💻 Run your salary reconciliation from Command Prompt & view it on your phone

A plain-English, step-by-step guide. Two parts:

- **Part A** — Run the reconciliation on your PC using Command Prompt (`cmd`).
- **Part B** — Open the finished reports on your mobile phone.

You only touch the PC once (Part A). After that you can check everything from your phone.

---

## Part A — Run it from Command Prompt (on your Windows PC)

### What you need in ONE folder
Everything must sit **together in a single folder** — the script won't find the files otherwise.
This is your **"desktop salary folder"** (in Google Drive:
`https://drive.google.com/drive/folders/1hoJ1-t6zCeptcsHAnpdfSvYQlTC6Mu6p`,
mirrored locally on your `D:` drive).

That folder must contain:

| File | What it is |
|---|---|
| `reconcile.py` | the pipeline script (the engine) |
| `run_april26.bat` | the one-click runner |
| `apr26_FULL_monthly_sheet.xlsx` | the salary sheet (main input) |
| `FORMAT-APRIL_2026_DELHI.xlsx` | ECR file 1 |
| `FORMAT_APRIL_2026_STEAGE.xlsx` | ECR file 2 |
| `FORMAT-APRIL_2026_DMART.xlsx` | ECR file 3 |
| `ESIC_CONSOLIDATED_APR_2026.xlsx` | the ESI "future" sheet |

> **Can't find the folder on your PC?** Open Command Prompt and run:
> ```
> dir /s /b D:\reconcile.py
> ```
> That prints the full path where it lives. `cd` into that folder for the steps below.

### The easy way (recommended) — double-click
1. Open the "desktop salary folder".
2. **Double-click `run_april26.bat`.**
3. A black Command Prompt window opens and runs everything. Wait until it says:
   `===== DONE - check April26_Final_Complete.xlsx and April26_Reconciliation_Report.xlsx =====`
4. Press any key to close.

That's it — the `.bat` **is** the command prompt run. It does everything below automatically.

### The manual way — type it yourself in Command Prompt
Use this if the double-click fails, or you just want to see what it does.

1. Press **Windows key**, type `cmd`, press **Enter**. A black window opens.
2. Go into your salary folder (change the path to your real one):
   ```
   cd /d "D:\path\to\desktop salary folder"
   ```
3. First time only — install the two libraries the script needs:
   ```
   pip install pandas openpyxl
   ```
4. Run the reconciliation (this is the exact command from `run_april26.bat`):
   ```
   python reconcile.py --salary "apr26_FULL_monthly_sheet.xlsx" --ecr "FORMAT-APRIL_2026_DELHI.xlsx" "FORMAT_APRIL_2026_STEAGE.xlsx" "FORMAT-APRIL_2026_DMART.xlsx" --future "ESIC_CONSOLIDATED_APR_2026.xlsx" --month 2026-04 --out-prefix April26
   ```
   (One long line — copy-paste the whole thing, then press Enter.)

### What you get (the outputs)
When it finishes, two new files appear **in the same folder**:

| Output file | What's inside |
|---|---|
| `April26_Final_Complete.xlsx` | the full corrected salary sheet |
| `April26_Reconciliation_Report.xlsx` | the checks, summaries & ESI audit |

> **Doing a different month?** Same command — just swap the file names, change
> `--month YYYY-MM`, and change `--out-prefix` (e.g. `May26`). See §4 of
> `docs/SALARY_KNOWLEDGEBASE.md` for the general form.

---

## Part B — View the results on your mobile phone

You don't run anything on the phone. You just **open the files that Part A produced**.
Because the folder is a **Google Drive** folder, the new output files sync to the cloud
automatically, so they show up on your phone within a minute or two.

### Option 1 — Google Drive app (best for the Excel reports)
1. Install / open the **Google Drive** app and sign in as **dinesh@impressionsgroup.in**.
2. Open the folder **SALARY DATA 2026-27 → desktop salary folder**.
3. Tap **`April26_Reconciliation_Report.xlsx`** to read the summary & checks,
   or **`April26_Final_Complete.xlsx`** for the full sheet.
   - For a clean spreadsheet view, install the **Google Sheets** app too — Drive
     will offer to open Excel files in it.

> If the file doesn't appear yet, the PC hasn't finished syncing. Make sure Google
> Drive for Desktop is running on the PC, wait a minute, then pull-to-refresh in the app.

### Option 2 — The interactive dashboards (best for a quick at-a-glance view)
This repo already ships **self-contained dashboard web pages** — one file, opens in any
phone browser, no internet needed once downloaded:

- `docs/pf-salary-reconciliation/april-2026/dashboard_April2026.html` — April 2026
- `docs/pf-salary-reconciliation/dashboard.html` — full year FY2025-26

**To view on your phone:** put either `.html` file into your Google Drive (drag it into
any Drive folder on the PC), then in the Drive app tap it → **Open with → your browser**.
It renders as a normal web page with all your numbers.

### Option 3 — Just the headline numbers on your phone
If you only want the key figures, open `docs/SALARY_KNOWLEDGEBASE.md` (this same repo)
in the **GitHub mobile app** or GitHub in your phone browser. Section 2 ("Verified anchor
numbers") has the April-26 and full-year totals in a table.

---

## Quick reference card

| I want to… | Do this |
|---|---|
| Run it the easy way | Double-click `run_april26.bat` |
| Run it by hand | `cmd` → `cd /d "<folder>"` → paste the `python reconcile.py …` line |
| Find the folder on my PC | `dir /s /b D:\reconcile.py` |
| See results on phone (numbers) | Google Drive app → `April26_Reconciliation_Report.xlsx` |
| See results on phone (dashboard) | Put `dashboard_April2026.html` in Drive → open in phone browser |

---

## If something goes wrong

| Message / problem | Fix |
|---|---|
| `'python' is not recognized` | Python isn't installed / not on PATH. Install from python.org and tick **"Add Python to PATH"**. |
| `'pip' is not recognized` | Same as above — reinstall Python with the PATH box ticked. |
| `No such file or directory` / file not found | A file name is mistyped, or you're not `cd`'d into the right folder. Run `dir` to see what's actually there. |
| `ModuleNotFoundError: pandas` | Run `pip install pandas openpyxl` first. |
| Output files don't reach my phone | Google Drive for Desktop isn't running / not synced. Start it on the PC, wait, refresh the Drive app. |

---

*Companion to `docs/SALARY_KNOWLEDGEBASE.md` — see §4 for the methodology and §3 for where every file lives.*
