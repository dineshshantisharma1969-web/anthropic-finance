# Payroll module — data drop

Put each month's **reconciled per-employee CSV** here (the output of `reconcile.py`,
same columns as `ACTION_NEEDED_<Month>.csv` / the full monthly sheet), then load it:

```bash
python ../load_period.py --csv april2026.csv --period 2026-04 --fy 2026-27 \
    --host <host> --user <user> --password <pw> --dbname postgres
```

Large full monthly sheets (>10 MB) live in Google Drive (see
`docs/SALARY_KNOWLEDGEBASE.md` §3) and are run locally; only commit CSVs here if
they are small enough and you want them version-controlled.
