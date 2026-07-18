---
type: map
domain: all
title: Telegram query bots (n8n)
status: active
tags: [telegram, n8n, query, bot]
created: 2026-07-18
---

# 📱 Telegram query bots (n8n)

Ask compliance questions from Telegram. All run on the n8n instance
(kappulearnn8n.app.n8n.cloud, project "Kalpana sharma") and answer via Claude Sonnet 5.

| Bot | Workflow ID | Domain | Data source |
|---|---|---|---|
| **GST Notice Tracker Query Bot** | `PPBdXvLYmi7dDOjF` | GST notices | **Live** — downloads the GST tracker xlsx from Drive each query |
| **ISPL Salary Query Bot v2** | `WoWBrmA71JbpUbh0` | Salary / PF / ESI | (salary data) |
| **ISPL IT Notice Query Bot** | `7ODMVOl5TrMMQKnH` | Income Tax notices | **Embedded** curated knowledge (AY2015-16 → AY2023-24) |

## ISPL IT Notice Query Bot — built 18-Jul-2026

- Telegram bot credential: **"ISPL IT NOTICE TRACKER"**. Flow: Telegram Trigger → Answer IT
  Question (Claude Sonnet 5 + 5-turn memory) → Send Telegram Reply.
- Knowledge embedded in the agent system prompt from [[2026-01-income-tax-ay2023-24-survey-search]]
  and [[income-tax-ay2015-to-2019-reassessment]]. Plain-text replies, INR lakh/crore formatting.
- **Static snapshot** — when IT notices change, ask Claude Code to refresh the agent's system
  message (the IT extract files are one-time snapshots, not a daily-synced tracker like GST).
- Example questions: "total proposed addition for AY2023-24?", "what are the 7 survey heads?",
  "status of the Netra Enterprises matter?", "which AYs have PF/ESI disallowance?"

## Refresh / maintenance

- GST bot is self-refreshing (reads Drive live). IT bot needs a prompt update when notices move.
- To extend the IT bot to read live from Drive later, mirror the GST bot's
  download → extract → build-JSON → agent pattern against the IT notices files.
