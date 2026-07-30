# Running ISPL Payroll on your PC — and uploading April / May

The payroll console is an **app you run on a computer**, not a website that's
already online. It saves everything to your database (your Supabase), so once
it's running you upload your processed files through the browser.

You only do **Setup** once. After that it's just "Start it" and "Upload".

---

## What you need (once)

- **Python** — the same one you use to run `reconcile.py`.
- **Your database connection** — host, user, password (your Supabase details).

---

## Setup (once)

1. Open the `erp/payroll/webui` folder.
2. **Windows:** double-click **`run.bat`**. **Mac:** run **`./run.sh`** in Terminal.
   The first time, it creates a settings file and opens it.
3. In that settings file, fill in your **database connection** and a made-up
   **secret string**, then **save and close** it.
4. Run `run.bat` / `run.sh` again. It will:
   - install what it needs,
   - create the payroll tables in your database,
   - ask you to set an **admin password** (remember it),
   - start the app.
5. You'll see: `Open this in your browser: http://127.0.0.1:8000`.
   Open that address in Chrome/Edge. Log in with **dinesh** + the password you set.

> Keep the black window (or Terminal) open while you use the app — closing it
> stops the app. To use it again another day, just run `run.bat` / `run.sh`.

---

## Uploading your April and May processed files

"Processed file" = the per-employee CSV your `reconcile.py` produces (the one
with EMPCODE, REVISED_PF, ECR_PF, NETPAYABLE, ACTION_REASON, …). If yours is an
Excel file, save that sheet as **CSV** first (File → Save As → CSV).

1. In the app, click **＋ Load month** (top-right).
2. Set **Period** to **April 2026** (`2026-04`).
3. Click **Choose File** and pick your April processed CSV.
4. Click **Load month**. Done — April now appears in the **Period** selector with
   its KPIs, action list, and Golden-Rule checks.
5. Repeat for **May** (`2026-05`).

That's it. Switch between months with the **Period** dropdown at the top.

If you upload the same month again later (say a corrected file), it **replaces**
that month's rows and records it as a new audited run — safe to redo.

---

## Adding your team later (optional)

To let Amit, Vishnu, Ajay, and Pradeep log in and use the readiness board:

```
python manage_users.py add amit   --role clerk --name "Amit Singh"
python manage_users.py own amit salary          # Amit owns the salary input
python manage_users.py add ajay   --role clerk --name "Ajay Sharma"
python manage_users.py own ajay pf
python manage_users.py add pradeep --role clerk --name "Pradeep"
python manage_users.py own pradeep esi
python manage_users.py add asha   --role approver --name "Asha Rao"
```

(Run these in the same `webui` folder with your settings loaded.)

---

## Common hiccups

- **"python is not recognized"** → Python isn't on your PATH. Reinstall Python
  and tick "Add Python to PATH", or use `py` instead of `python`.
- **Database error on setup** → re-open your settings file and check the host /
  user / password. The whole `ERP_DB=...` must be one line.
- **Page won't open** → make sure the window that runs the app is still open, and
  use exactly `http://127.0.0.1:8000`.
- **Want the team to reach it from their own PCs?** localhost only works on your
  machine — that needs hosting it on a server. Ask and we'll set that up.
