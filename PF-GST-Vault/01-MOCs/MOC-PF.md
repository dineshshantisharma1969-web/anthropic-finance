---
type: moc
domain: pf
tags: [domain/pf, moc]
---

# MOC — Provident Fund

Hub for all PF notes: scheme rules, reconciliation cases, circulars, and wage-floor rules.

## Reconciliation Cases
- [[ESI-Washing-Reallocation]] — PF/ESI M13 FINAL reconciliation & ESI reallocation, FY2025-26

## Open Cases (Dataview)
```dataview
TABLE status, opened, deadline
FROM "02-PF/Reconciliation-Cases"
WHERE type = "case" AND status = "open"
SORT opened DESC
```

## Circulars & Notifications (Dataview)
```dataview
TABLE issued_by, issued_date, effective_date
FROM "02-PF/Circulars-Notifications"
WHERE type = "circular"
SORT effective_date DESC
```

## Scheme 2026
_Notes on the PF Scheme 2026 go under `02-PF/Scheme-2026/`._

## Wage-Floor Rules
_Notes on wage-floor / minimum-wage rules go under `02-PF/Wage-Floor-Rules/`._
