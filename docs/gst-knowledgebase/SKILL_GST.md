---
name: gst-law-research
description: >
  GST (India) law research and compliance skill. Use whenever the user asks about
  GST law, rules, notifications, circulars, returns, ITC, RCM, rates, valuation,
  registration, e-invoicing/e-way bills, departmental notices, or GST litigation.
  Answers are built ONLY from the loaded law library in
  docs/gst-knowledgebase/law-library/ (+ linked Drive source PDFs) — never from
  model memory. Every answer carries citations with effective dates.
---

# GST Law Research Skill

## Golden Rules (never violated)

1. **No answer from memory.** Every legal statement must trace to a document in the
   law library (or a source the user provides in-session). If the library doesn't
   cover it, say exactly that and name the official source to fetch
   (cbic-gst.gov.in › GST Law).
2. **Cite precisely, with dates.** Format: `S.16(2)(c) CGST Act (as amended w.e.f.
   01-01-2022)` · `Rule 36(4) CGST Rules` · `NN 13/2017-CT(R) dt 28-06-2017` ·
   `Circular 172/04/2022-GST`. A citation without its effective date is incomplete —
   GST provisions change; the date IS part of the answer.
3. **Check the amendments log before quoting** any section/rule
   (`law-library/acts/INDEX.md` § amendments). What was true for FY2023-24 may be
   wrong for FY2026-27.
4. **For cases: limitation first.** Before any analysis of a notice/order, compute
   and state the reply/appeal deadline. A brilliant argument filed late is worthless.
5. **Period-match the text version.** The library holds more than one version of the
   CGST Act; answer from the version in force for the tax period in question:
   - **Current periods** → `law-library/acts/cgst-act-2017/` (compilation as on
     **01-01-2026**; flag anything after that date as unverified).
   - **Old-period matters (FY 2017-18 → FY 2020-21)** → `law-library/archive/
     cgst-act-2017-as-on-30092020/` — **official CBIC** consolidated text as on
     30-09-2020. Never cite it for later periods (e.g. it predates S.16(2)(aa)).
   - Old-period gaps (FY 2021-22 → 2025-26 as-it-stood text) → reconstruct from the
     01-01-2026 text's footnoted amendment history, and say you did so.
   The `archive/` folder is excluded from the Telegram bot's retrieval by design;
   old-period questions are desk-research questions, not bot questions.

## Source hierarchy (higher overrides lower)

1. **Act** (CGST/IGST/UTGST/SGST/Cess) — as amended, at the relevant date
2. **Rules** (CGST Rules 2017 etc.)
3. **Notifications** (have force of law where the Act delegates — esp. rate NNs)
4. **Orders / Removal-of-Difficulty orders**
5. **Circulars** (bind the department, NOT the taxpayer — cite them FOR the taxpayer
   when favourable; they cannot override the Act — *so hold multiple HC decisions*)
6. **FAQs / portal advisories / press releases** (no legal force — practical guidance only)
7. **Case law**: SC > jurisdictional HC > other HC > AAAR/AAR (AAR binds only the
   applicant — flag this whenever citing one)

## Answer workflow

1. Restate the question with the relevant **tax period** (law varies by date).
2. Retrieve: search `law-library/` indexes → open the source doc(s).
3. Reason over the retrieved text; quote operative words verbatim where they decide the issue.
4. Cross-check amendments log + any notification that modifies the provision.
5. Answer format: **Position** (one line) → **Basis** (citations w/ dates) →
   **Contrary view / risk** (if any exists, say so honestly) → **Action**.
6. If a `positions/POSITIONS.md` entry exists on the issue, apply it and say so —
   consistency across periods matters in assessment.

## Returns discipline

Track in `returns/RETURNS_CALENDAR.md`: GSTR-1 (outward), GSTR-3B (summary+payment),
GSTR-9/9C (annual), plus ITC-04, ISD returns as applicable — per GSTIN. Rule:
**never state a due date without checking for extension notifications for that period.**

**Before filing every GSTR-1: run the books-vs-portal reconciliation**
(`recon/SKILL_GSTR1_RECON.md`, Rules G1–G4) — bill no, taxable value, rate and
GST amount must match invoice-by-invoice; exceptions are actioned via the
worklist (BOOKS_ONLY first — the interest clock runs on those).

## Update discipline

- New notification/circular arrives → add one row to the relevant INDEX before anything else.
- Amendment Act / Finance Act → update the amendments log with effective-date notification.
- Case order received → update `cases/CASE_TRACKER.md` same day (deadlines!).
- Position taken in any filing/reply → record in `positions/POSITIONS.md` with citations.
