-- =====================================================================
-- ISPL ERP — Payroll module schema (Postgres 14+)
-- =====================================================================
-- The first module of the Impressions Group ERP.
--
-- Design intent (vs. the flat one-table-per-month spreadsheet/CSV world):
--   * ONE database that ACCUMULATES periods (Apr, May, ... side by side),
--     instead of a new table per month.
--   * Master data (employees, sites) is stored ONCE and referenced, so an
--     employee who appears in 14 months is one row in `employee`, not 14.
--   * Every load is an auditable event (`reconciliation_run`) that records
--     who ran it, against which source files, and whether the three Golden
--     Rules held (PF gap = 0, net drift = 0).
--   * ACTION_NEEDED rows become tracked tickets (`action_item`) with a
--     status lifecycle — not a static CSV that is regenerated and lost.
--
-- Golden Rules (never violated — enforced/validated by the loader):
--   1. Σ REVISED_PF = ECR_PF               (per period)
--   2. Σ REVISED_ESIC = Future-sheet ESIC  (per period)
--   3. NET PAYABLE never changes           (drift 0)
--
-- Idempotent: safe to run repeatedly. Uses IF NOT EXISTS throughout.
-- To wipe and rebuild from scratch, run drop_all.sql first (see README).
-- =====================================================================

CREATE TABLE IF NOT EXISTS employee (
    emp_code      text PRIMARY KEY,          -- business key (EMPCODE)
    full_name     text NOT NULL,
    epf_no        text,                       -- populated when the full sheet is loaded
    uan_no        text,
    esi_no        text,
    first_seen    date,                       -- first period this employee appears in
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS site (
    site_code     text PRIMARY KEY,           -- SITECODE
    site_name     text NOT NULL,
    site_state    text,                       -- SITESTATE
    client_name   text,                       -- derived from site_name today; own column later
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- A payroll period = one month's run. Status drives the module workflow.
CREATE TABLE IF NOT EXISTS salary_period (
    id                serial PRIMARY KEY,
    period            text NOT NULL UNIQUE,   -- 'YYYY-MM', e.g. '2026-04'
    fy                text NOT NULL,          -- '2026-27'
    status            text NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft','reconciled','filed','closed')),
    net_payable_anchor numeric,               -- sacrosanct net (Golden Rule 3 anchor)
    ecr_pf_anchor     numeric,                -- Σ ECR PF filed (Golden Rule 1 anchor)
    future_esi_anchor numeric,                -- Σ Future ESI (Golden Rule 2 anchor)
    notes             text,
    created_at        timestamptz NOT NULL DEFAULT now()
);

-- Every load of a period is an auditable run: who, when, from what, and
-- whether the Golden Rules held. Never deleted — this is the audit trail.
CREATE TABLE IF NOT EXISTS reconciliation_run (
    id            serial PRIMARY KEY,
    period_id     integer NOT NULL REFERENCES salary_period(id),
    run_at        timestamptz NOT NULL DEFAULT now(),
    run_by        text,                       -- who kicked off the load
    source_files  text,                       -- salary sheet + ECR files used
    rows_loaded   integer,
    sum_revised_pf   numeric,
    sum_ecr_pf       numeric,
    pf_gap           numeric,                 -- sum_revised_pf - sum_ecr_pf  (Rule 1: must be 0)
    sum_net_payable  numeric,
    net_drift        numeric,                 -- vs period anchor (Rule 3: must be 0)
    checks           jsonb,                   -- full check set (C1..C10, C-MW)
    notes         text
);

-- One row per employee-per-site-per-period. The heart of the module.
-- (Same employee at two sites in one month => two rows: PF_ANCHOR + PF_SECONDARY.)
CREATE TABLE IF NOT EXISTS payroll_row (
    id                       bigserial PRIMARY KEY,
    period_id                integer NOT NULL REFERENCES salary_period(id),
    run_id                   integer NOT NULL REFERENCES reconciliation_run(id),
    emp_code                 text NOT NULL REFERENCES employee(emp_code),
    site_code                text NOT NULL REFERENCES site(site_code),
    normal_days              numeric,
    adj_working_days         numeric,
    gross_amt                numeric,   -- original
    revised_gross            numeric,
    net_payable              numeric,
    ecr_pf                   numeric,
    revised_pf               numeric,
    revised_esic             numeric,
    future_esi               numeric,
    rule_applied             text,      -- PF_ANCHOR / PF_SECONDARY / ESI_ONLY / NO_PF_NO_ESI / SKIP_ZERO_BASIC
    monthly_gross_projection numeric,
    real_full_month_gross    numeric,
    overpaid_vs_rate         numeric,
    action_needed            boolean NOT NULL DEFAULT false,
    action_reason            text,
    excess_salary            numeric
    -- No business unique key: one employee can legitimately have several lines
    -- at the same site in one period (e.g. a PF_ANCHOR line plus a PF_SECONDARY
    -- multi-slot line). The grain is "one line of the reconciliation output".
    -- Idempotent re-loads are handled by delete-by-period in load_period.py,
    -- not by a unique constraint. (idx_payroll_emp_site below speeds lookups.)
);

-- The workflow layer: every ACTION_NEEDED payroll row becomes a ticket that
-- someone owns and resolves. This is what a spreadsheet cannot do.
CREATE TABLE IF NOT EXISTS action_item (
    id             bigserial PRIMARY KEY,
    payroll_row_id bigint NOT NULL REFERENCES payroll_row(id) ON DELETE CASCADE,
    period_id      integer NOT NULL REFERENCES salary_period(id),
    emp_code       text NOT NULL REFERENCES employee(emp_code),
    site_code      text NOT NULL REFERENCES site(site_code),
    reason         text,
    excess_salary  numeric,
    status         text NOT NULL DEFAULT 'open'
                     CHECK (status IN ('open','investigating','resolved','waived')),
    assigned_to    text,
    resolution_note text,
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now()
);

-- Application users + their role. Auth is enforced server-side; the role gates
-- who may work tickets, correct figures, and file/reopen periods.
--   viewer   → read-only
--   clerk    → + work tickets, correct figures on open periods
--   approver → + file/close periods, reopen locked periods
--   admin    → + manage users
CREATE TABLE IF NOT EXISTS app_user (
    id            serial PRIMARY KEY,
    username      text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    full_name     text,
    role          text NOT NULL DEFAULT 'viewer'
                    CHECK (role IN ('viewer','clerk','approver','admin')),
    active        boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now()
);

-- Immutable audit trail of every change to a financial figure or a period's
-- status. Never updated or deleted — this is the "who changed what, when, and
-- why" record that makes a corrected number defensible to an auditor / EPFO.
CREATE TABLE IF NOT EXISTS figure_change (
    id           bigserial PRIMARY KEY,
    entity       text NOT NULL,            -- 'payroll_row' or 'salary_period'
    entity_id    bigint NOT NULL,          -- row id / period id
    period_id    integer REFERENCES salary_period(id),
    emp_code     text,                     -- denormalized for quick filtering
    field        text NOT NULL,            -- e.g. 'revised_pf', 'status'
    old_value    text,
    new_value    text,
    changed_by   text,
    reason       text NOT NULL,            -- reason is mandatory for a financial edit
    changed_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_change_period ON figure_change (period_id);
CREATE INDEX IF NOT EXISTS idx_change_entity ON figure_change (entity, entity_id);

CREATE INDEX IF NOT EXISTS idx_payroll_period  ON payroll_row (period_id);
CREATE INDEX IF NOT EXISTS idx_payroll_emp     ON payroll_row (emp_code);
CREATE INDEX IF NOT EXISTS idx_payroll_site    ON payroll_row (site_code);
CREATE INDEX IF NOT EXISTS idx_payroll_emp_site ON payroll_row (period_id, emp_code, site_code);
CREATE INDEX IF NOT EXISTS idx_payroll_action  ON payroll_row (action_needed) WHERE action_needed;
CREATE INDEX IF NOT EXISTS idx_action_status   ON action_item (status);
CREATE INDEX IF NOT EXISTS idx_action_period   ON action_item (period_id);

-- ---------------------------------------------------------------------
-- Views: the things you actually look at.
-- ---------------------------------------------------------------------

-- Per-period rollup: totals + Golden-Rule position at a glance.
CREATE OR REPLACE VIEW v_period_summary AS
SELECT p.period, p.fy, p.status,
       count(r.*)                                  AS rows,
       count(*) FILTER (WHERE r.action_needed)     AS action_rows,
       round(sum(r.revised_pf))                    AS revised_pf,
       round(sum(r.ecr_pf))                        AS ecr_pf,
       round(sum(r.revised_pf) - sum(r.ecr_pf))    AS pf_gap,
       round(sum(r.net_payable))                   AS net_payable,
       round(sum(r.excess_salary))                 AS excess_salary
FROM salary_period p
LEFT JOIN payroll_row r ON r.period_id = p.id
GROUP BY p.period, p.fy, p.status
ORDER BY p.period;

-- Open action workload by period and reason.
CREATE OR REPLACE VIEW v_open_actions AS
SELECT p.period, a.reason, a.status,
       count(*)                 AS items,
       round(sum(a.excess_salary)) AS excess_salary
FROM action_item a
JOIN salary_period p ON p.id = a.period_id
GROUP BY p.period, a.reason, a.status
ORDER BY p.period, excess_salary DESC NULLS LAST;

-- Month-over-month per employee (net + PF), for the comparison a single
-- spreadsheet can't give you.
CREATE OR REPLACE VIEW v_emp_month_over_month AS
SELECT r.emp_code, e.full_name, p.period,
       round(sum(r.net_payable)) AS net_payable,
       round(sum(r.revised_pf))  AS revised_pf
FROM payroll_row r
JOIN salary_period p ON p.id = r.period_id
JOIN employee e      ON e.emp_code = r.emp_code
GROUP BY r.emp_code, e.full_name, p.period
ORDER BY r.emp_code, p.period;
