-- Wipe the payroll module (dev/reset only). Order respects FKs.
DROP VIEW  IF EXISTS v_emp_month_over_month;
DROP VIEW  IF EXISTS v_open_actions;
DROP VIEW  IF EXISTS v_period_summary;
DROP TABLE IF EXISTS action_item;
DROP TABLE IF EXISTS payroll_row;
DROP TABLE IF EXISTS reconciliation_run;
DROP TABLE IF EXISTS salary_period;
DROP TABLE IF EXISTS site;
DROP TABLE IF EXISTS employee;
