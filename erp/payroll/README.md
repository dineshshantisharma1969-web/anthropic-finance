# ISPL ERP — Payroll module

The first module of the Impressions Group ERP. It gives the monthly PF/ESI salary
reconciliation a permanent, queryable home — turning the per-month CSV/spreadsheet
runs into an accumulating database with an **audit trail** and an **action-item
workflow**.

This is the foundation every later feature (web UI, month-by-month P&L, GL) reads
from. It does **not** replace the reconciliation logic in
`docs/pf-salary-reconciliation/` — it is the *destination* for that logic's output.

## Why this exists (vs. the spreadsheet world)

| Spreadsheet / CSV today | This module |
|---|---|
| One workbook per month, thrown away & regenerated | One DB that **accumulates** periods (Apr, May, …) |
| Employee repeated in every month's file | Employee stored **once** in `employee`, referenced |
| No record of who ran what, when | Every load is a `reconciliation_run` (who / when / from what / checks) |
| ACTION_NEEDED is a static CSV | Each action row is a **tracked ticket** with a status lifecycle |
| No month-over-month view | `v_emp_month_over_month`, `v_period_summary` |

## Schema (see `schema.sql`)

```
employee ─┐                 site ─┐
          │                       │
          ▼                       ▼
salary_period ──< reconciliation_run ──< payroll_row ──< action_item
   (one per month)   (one per load,        (one line per      (one per
                      audit trail)          emp·site·period)    ACTION_NEEDED row)
```

- **`employee` / `site`** — master data, stored once.
- **`salary_period`** — one row per month (`2026-04`, …) with a `status`
  (`draft → reconciled → filed → closed`) and the Golden-Rule anchors.
- **`reconciliation_run`** — the audit trail: every load records who ran it, the
  source files, row count, and the Golden-Rule check results (PF gap, net drift).
- **`payroll_row`** — the heart: one line per employee·site·period. Holds original
  **and** revised figures plus the rule applied. No business unique key — an
  employee can legitimately have a `PF_ANCHOR` line **and** a `PF_SECONDARY`
  multi-slot line at the same site in one month (24 such cases in the April fixture).
- **`action_item`** — every `ACTION_NEEDED=Y` row becomes a ticket
  (`open → investigating → resolved → waived`), with `assigned_to` and a resolution note.

### Views
- `v_period_summary` — per-period totals + Golden-Rule position at a glance.
- `v_open_actions` — open action workload by period and reason.
- `v_emp_month_over_month` — per-employee net & PF across months.

### The three Golden Rules (validated on every load)
1. `Σ REVISED_PF = ECR_PF` → `reconciliation_run.pf_gap` must be 0.
2. `Σ REVISED_ESIC = Future ESI` → tracked as `esi_future_gap` in `checks`.
3. **Net payable never changes** → `reconciliation_run.net_drift` vs the period anchor must be 0.

## Usage

```bash
pip install psycopg2-binary

# 1. create the schema (once per database)
psql "$DB" -f schema.sql

# 2. load a reconciled month (repeatable — a re-load replaces that period's
#    rows and records a fresh audited run)
python load_period.py --csv <reconciled_month>.csv \
    --period 2026-04 --fy 2026-27 \
    --host <host> --port 5432 --user <user> --password <pw> --dbname postgres \
    --run-by dinesh --source-files "apr26 sheet + DELHI/STEAGE/DMART ECR" \
    --net-anchor 259937250        # optional: sacrosanct net anchor for Rule 3
```

The `--csv` file is the per-employee output of `reconcile.py` (same columns as
`ACTION_NEEDED_<Month>.csv` / the full monthly sheet). Column matching is
case-insensitive and tolerant of the `GROSS AMT` space; extra columns are ignored.

To point at the production Supabase, use the same connection details as the
existing `load_maharashtra_to_postgres.py` loader.

## Validation status

Validated end-to-end on Postgres 16 against the committed April action subset
(`docs/pf-salary-reconciliation/april-2026/ACTION_NEEDED_April2026.csv`,
4,974 rows):

- Schema applies clean; loader ingests, upserts 4,899 employees + 658 sites,
  creates 4,974 action tickets.
- Idempotent: re-loading the period keeps 4,974 rows (no double-count) and adds a
  2nd audited run.
- **Cross-check:** loaded `Σ EXCESS_SALARY = ₹5,44,58,591`, which ties exactly to
  the verified April anchor in `docs/SALARY_KNOWLEDGEBASE.md` §2.

> Note: that fixture is the **action subset**, used to prove the pipeline. Loading
> the full monthly sheet (all ~21,152 rows) is the same command with the full CSV,
> and is what populates a period for real. **May 2026 loads the same way** once its
> reconciled CSV is committed to `erp/payroll/data/` or supplied.

## Next increments (not in this change)
1. **DB-backed web UI** — browse periods, work the action list as tickets.
2. **Reconciliation-as-a-service** — upload salary sheet + ECR → results land here.
3. **Auth + roles** — view / approve / file.
4. **P&L / GL modules** reading the same database.
