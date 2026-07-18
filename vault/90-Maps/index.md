---
type: map
domain: all
title: Vault Index
status: active
tags: [moc, index]
created: 2026-07-18
---

# 🧭 Vault Index

Start here. See [[README]] for how the vault is organised, and **[[ARCHITECTURE]]** for the
whole pipeline (sources → process → consolidated → dashboards) as one control panel.

## By domain

- **[[MOC-Salary]]** — PF / ESI / wage-code reconciliation (richest area today)
- **[[MOC-GST]]** — GST law, rules, notices (tracker: 34 cases, ₹60.71 Cr)
- **[[MOC-Income-Tax]]** — Income Tax notices (AY2015-16 → AY2023-24 survey/search)
- **[[compliance-dashboard]]** — unified GST + IT + Salary dashboard (live-generated)
- **[[telegram-query-bots]]** — ask GST / IT / Salary from Telegram

## By lifecycle (folders)

| Folder | Count today | Purpose |
|---|--:|---|
| `00-Inbox/` | — | Drop raw captures here; I sort them |
| `10-Law/` | scaffold | Verbatim GST / Income-Tax / PF-ESI source |
| `20-Rules/` | 6 | ISPL working rules |
| `30-Notices/` | scaffold | Live GST / IT notices |
| `40-Workings/` | 5 | Dated recon runs & analyses |

## Ask me anything like…

- "What's our 50% wage-code rule and how are day-rated employees handled?" → [[wage-code-50pct-rule]]
- "How does FY25-26 PF tie to the ECR?" → [[2026-07-pf-reconciliation-fy2526]]
- "Draft a reply to this GST notice" → paste into `00-Inbox/`, I pull the relevant law + rules.
