-- ============================================================================
-- Cross-year queries: Maharashtra FY2024-25  +  FY2025-26  (same Supabase DB)
-- ============================================================================
-- The two datasets live in two tables with DIFFERENT column names:
--   * maharashtra_salary_2024_25   (this repo's loader; snake_case columns)
--   * <the 25-26 table>            (ISPL v4 columns: EMPCODE, FULLNAME, MONTH,
--                                   BRANCHNAME, "GROSS AMT", REVISED_PF, ECR_PF,
--                                   "ESIC.1", RULE_APPLIED, REVISED_NET_PAYABLE, ...)
--
-- I could not read the live DB from here, so TWO things must be confirmed once:
--   (1) the 25-26 TABLE NAME
--   (2) whether the 25-26 columns are quoted-verbatim ("GROSS AMT") or normalised
--       (gross_amt).  Run STEP 0 to find out, then use the matching view below.
-- ============================================================================

-- STEP 0 — introspect (run once; tells you the table name + exact column names)
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public' AND table_name ILIKE '%salary%';

SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = '<TABLE_2025_26>'          -- <-- paste the name STEP 0 returned
  AND column_name ILIKE ANY (ARRAY['empcode','fullname','month','branchname',
        'gross%amt%','revised_pf','ecr_pf','esic%','rule_applied','sitestate'])
ORDER BY column_name;

-- ============================================================================
-- OPTION A — 25-26 columns kept VERBATIM (need double quotes for spaces/caps)
--   Most common when the loader used pandas.to_sql / COPY with original headers.
-- ============================================================================
CREATE OR REPLACE VIEW v_salary_all_years AS
SELECT '2024-25'::text          AS fy,
       month                    AS month,
       emp_code                 AS emp_code,
       name                     AS name,
       branch                   AS branch,
       gross                    AS gross,
       revised_pf               AS revised_pf,
       ecr_pf_capped            AS ecr_pf,
       esi_emp                  AS revised_esi,
       pf_rule                  AS rule_applied
FROM   maharashtra_salary_2024_25
UNION ALL
SELECT '2025-26'::text,
       "MONTH",
       "EMPCODE"::text,
       "FULLNAME",
       "BRANCHNAME",
       "GROSS AMT"::numeric,
       "REVISED_PF"::numeric,
       "ECR_PF"::numeric,
       "ESIC.1"::numeric,
       "RULE_APPLIED"
FROM   <TABLE_2025_26>;          -- <-- paste the 25-26 table name

-- ============================================================================
-- OPTION B — 25-26 columns NORMALISED (lowercase, spaces->underscores, .->_ )
--   Use this instead of OPTION A if STEP 0 shows names like gross_amt, esic_1.
-- ============================================================================
-- CREATE OR REPLACE VIEW v_salary_all_years AS
-- SELECT '2024-25', month, emp_code, name, branch, gross, revised_pf,
--        ecr_pf_capped AS ecr_pf, esi_emp AS revised_esi, pf_rule AS rule_applied
-- FROM   maharashtra_salary_2024_25
-- UNION ALL
-- SELECT '2025-26', month, empcode::text, fullname, branchname, gross_amt,
--        revised_pf, ecr_pf, esic_1, rule_applied
-- FROM   <TABLE_2025_26>;

-- ============================================================================
-- EXAMPLE QUERIES (work once the view exists)
-- ============================================================================
-- One employee across BOTH years
SELECT fy, month, emp_code, name, revised_pf, revised_esi
FROM   v_salary_all_years
WHERE  emp_code = '20031508'
ORDER  BY fy, month;

-- Year-over-year PF & ESI totals
SELECT fy,
       round(sum(revised_pf))  AS pf_total,
       round(sum(revised_esi)) AS esi_total,
       count(DISTINCT emp_code) AS employees
FROM   v_salary_all_years
GROUP  BY fy
ORDER  BY fy;

-- Maharashtra-only slice from the combined view
SELECT month, round(sum(revised_pf)) AS pf
FROM   v_salary_all_years
WHERE  fy = '2024-25'
GROUP  BY month
ORDER  BY month;
