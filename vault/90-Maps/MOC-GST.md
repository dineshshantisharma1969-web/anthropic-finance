---
type: map
domain: gst
title: MOC — GST
status: active
tags: [moc, gst]
created: 2026-07-18
---

# 🗺️ MOC — GST

> Scaffold. Populate as you add law and notices. Workflow: paste notice/section text into
> `00-Inbox/`, and I atomize it into `10-Law/GST/` (verbatim) and `30-Notices/` (live cases).

## Law (`10-Law/GST/`)

- _None yet._ Add sections, rules, circulars, notifications as verbatim [[_templates/law|law]] notes.

## Rules (`20-Rules/`, domain: gst)

- _None yet._ ISPL's interpretations / positions.

## Notices (`30-Notices/`, domain: gst)

- _None yet._ One dated [[_templates/notice|notice]] note per ASMT-10 / DRC / SCN.

## Common query patterns (once populated)

- "What's our position on ITC reversal for [X]?" — pulls law + rule notes
- "Draft an ASMT-10 reply for FY22-23" — pulls law *as it stood in FY22-23* (via
  `effective_from`/`effective_to`) + our rule + supporting workings
