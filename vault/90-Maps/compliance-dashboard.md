---
type: map
domain: all
title: Unified Compliance Dashboard (generator)
status: active
tags: [dashboard, n8n, gst, income-tax, salary, control-panel]
created: 2026-07-18
---

# 📊 Unified Compliance Dashboard

One self-contained HTML page across **GST · Income Tax · Salary/PF/ESI** — the capstone of
[[ARCHITECTURE|layer ④]]. Live-generated in n8n; regenerates the **same** Drive file each run
(stable URL).

- **Live file:** `COMPLIANCE_DASHBOARD.html` — Drive `1wa3WacHXVm6dFVBcikXqxrPUpsT8I9k0`
  ([open](https://drive.google.com/file/d/1wa3WacHXVm6dFVBcikXqxrPUpsT8I9k0/view))
- **Generator workflow:** `COuZRF1uYl1rQ47y` — "ISPL Compliance Dashboard generator (one-shot)".
  Manual trigger → re-run anytime for a fresh page.

## What it pulls (all three consolidated stores)

| Section | Source | Live? |
|---|---|---|
| GST — total demand, cases, overdue, reply-pending, top cases | GST tracker xlsx (AK Dash) `1ySb1_B2z7YOjMchvn8lxZWNqpuqbprK5`, "All Notices" sheet | **Live** (downloaded each run) |
| Salary — FY net payable, PF ECR, month table, ANUJ tie-out | `PIVOT_FY202526_LIVE_LINKED` `1tVwkaZPVZ9PMEkY952z6ZAQGL8UVuLUpSSC8HdymjFM` (Pivot_Month + PF_Tieout) | **Live** (Sheets API) |
| Income Tax — AY2023-24 heads + legacy matters | embedded snapshot from [[2026-01-income-tax-ay2023-24-survey-search]] | snapshot |

## Flow

`Start → Get Salary Pivot (Sheets) → Download GST Tracker → Extract All Notices →
Build Dashboard HTML (Code) → Upload Dashboard (PATCH media to fixed Drive file) → Report`

## Headline figures (18-Jul-2026)

- **GST:** ₹62.59 Cr demand · 34 cases · 24 overdue · 2 reply-pending (Haryana FY22-23, FY23-24)
- **Income Tax:** ₹9.38 Cr active proposed addition (AY2023-24), hearing 19-Jan-2026
- **Salary:** ₹293.30 Cr FY net payable · 2,35,077 rows · PF ECR ₹29.18 Cr (ANUJ ₹29.68 Cr)

## Refresh / extend

- **Refresh:** re-run workflow `COuZRF1uYl1rQ47y` (GST + salary update live; IT is a snapshot —
  ask Claude Code to refresh the IT block when notices change).
- **Schedule:** swap the manual trigger for a Schedule trigger to auto-regenerate (e.g. daily).
- **Next:** add due-date calendar alerts; make IT live-read like GST; add ESI/PT KPIs.
