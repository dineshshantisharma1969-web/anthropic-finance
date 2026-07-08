# Maharashtra FY2024-25 — queryable alongside 25-26 (Supabase/Postgres)

Loads the reconciled Maharashtra dataset into the **same Supabase** that holds your 25-26 data, so
both are queryable side by side (and your Telegram/n8n bot can reach FY24-25 too).

## Files
| File | What it is |
|---|---|
| `maharashtra_salary_2024_25.csv` | Consolidated PF + ESI per employee-month — **21,551 rows**, all 12 months (incl. May-24), one clean table |
| `load_maharashtra_to_postgres.py` | Creates table `maharashtra_salary_2024_25` and bulk-loads the CSV (idempotent) |

## Columns
`month, fy, emp_code, name, designation, epf_no, uan_no, site_name, branch, month_days,
worked_days, ncp, orig_basic_da, gross, orig_pf, ecr_pf_filed, ecr_pf_capped,
pf_above_1800_surplus, pf_source, pf_rule, revised_pf, revised_basic_da, adj_working_days,
pf_diff_parked, bd_monthly_projection, esic_wages, esi_emp, esi_co, esi_total, esi_above_21000,
esi_status`

## Run (in the session/PC that already connects to your Supabase)
```bash
pip install psycopg2-binary pandas
python load_maharashtra_to_postgres.py \
    --csv maharashtra_salary_2024_25.csv \
    --host aws-1-ap-northeast-2.pooler.supabase.com --port 5432 \
    --user postgres.rgfhqghwkiqwhwxjatsc --password IsplSalary2026 --dbname postgres
```
It drops & recreates `maharashtra_salary_2024_25`, loads all rows via `COPY`, and prints the row
count and control totals (revised PF ₹3,02,29,684). Re-runnable any time.

## Query alongside 25-26
The FY24-25 data lives in its own table `maharashtra_salary_2024_25` in the **same database** as
your 25-26 tables, so you can query or UNION across both:

```sql
-- May-24 below-15k / not-in-ECR (the enquiry that failed before)
SELECT emp_code, name, branch, orig_basic_da, orig_pf, pf_rule
FROM maharashtra_salary_2024_25
WHERE month = 'MAY-24' AND revised_pf = 0 AND orig_basic_da < 15000;

-- month-wise PF + ESI totals
SELECT month, round(sum(revised_pf)) AS pf, round(sum(esi_emp)) AS esi_emp
FROM maharashtra_salary_2024_25 GROUP BY month ORDER BY min(fy), month;

-- one employee across both years (adjust the 25-26 table/column names to yours)
SELECT '2024-25' fy, emp_code, month, revised_pf FROM maharashtra_salary_2024_25 WHERE emp_code = '20031508'
UNION ALL
SELECT fy, emp_code, month, revised_pf FROM <your_25_26_table> WHERE emp_code = '20031508';
```

## Cross-year queries (24-25 + 25-26)

The FY2025-26 data is a **different table with different column names** (ISPL v4 format —
`EMPCODE, FULLNAME, MONTH, BRANCHNAME, "GROSS AMT", REVISED_PF, ECR_PF, "ESIC.1", RULE_APPLIED,
REVISED_NET_PAYABLE`). Column mapping to this table:

| Common | Maharashtra 24-25 | 25-26 |
|---|---|---|
| employee | `emp_code` | `EMPCODE` |
| name | `name` | `FULLNAME` |
| month | `month` | `MONTH` |
| branch | `branch` | `BRANCHNAME` |
| gross | `gross` | `GROSS AMT` |
| revised PF | `revised_pf` | `REVISED_PF` |
| ECR PF | `ecr_pf_capped` | `ECR_PF` |
| revised ESI | `esi_emp` | `ESIC.1` |
| rule | `pf_rule` | `RULE_APPLIED` |

**`cross_year_queries.sql`** in this folder has: a STEP-0 introspection query (returns the 25-26
table name + exact column names), a harmonised `v_salary_all_years` view (two variants — verbatim
vs normalised column names, pick per STEP 0), and ready cross-year example queries. Run STEP 0
once, fill the 25-26 table name into the view, and both years query as one.

## Notes
- `fy = '2024-25'` on every row — the discriminator to filter/union against 25-26.
- ESI columns are populated where the employee is in the filed ESIC register; the ~91 ESIC-only
  employees/year (in the register but not the salary sheet) are not in this salary-centric table.
  For the full filed-ESI position see `../esi/`.
- Bot tip: point your n8n query at this table for FY24-25 questions, or add a `fy`/`state` filter so
  the same bot serves both years without mixing them.
