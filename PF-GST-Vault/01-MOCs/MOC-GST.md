---
type: moc
domain: gst
tags: [domain/gst, moc]
---

# MOC — GST

Hub for all GST notes: Act sections, circulars, notice replies, and the case log.

## Open Cases (Dataview)
```dataview
TABLE deadline, status
FROM "03-GST/Case-Log"
WHERE status = "open"
SORT deadline ASC
```

## Circulars (Dataview)
```dataview
TABLE issued_by, issued_date, effective_date
FROM "03-GST/Circulars"
WHERE type = "circular"
SORT effective_date DESC
```

## Act Sections
_Atomic provision notes go under `03-GST/Act-Sections/` (one section per note)._

## Notice Replies
_Drafted replies go under `03-GST/Notice-Replies/`._
