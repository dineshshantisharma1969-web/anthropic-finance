# 🧠 GST KNOWLEDGEBASE — Master Index

**The single entry point for all GST law, returns, cases and positions.**
Created: 2026-07-04 · Status: **SCAFFOLD — law library being loaded**
Pattern: identical to `docs/SALARY_KNOWLEDGEBASE.md` (the salary second brain).

> **How to use:** Start here. In any Claude conversation say
> *"Read docs/gst-knowledgebase/GST_KNOWLEDGEBASE.md in my anthropic-finance repo"*
> and the full GST context loads. Update this file in the same commit whenever a
> source is added, a case moves, or a position is taken.

> ⚠️ **Golden rule of this brain: NOTHING in the law library is written from an
> AI's memory.** Every Act section, rule, notification and circular is loaded from
> an official source document (CBIC / GST Council / gst.gov.in PDF), stored with
> its source link/Drive ID and date. AI reasons OVER these documents; it never
> substitutes for them. See `SKILL_GST.md` for the full methodology.

---

## 1. Structure

| Folder | Contents | Status |
|---|---|---|
| `SKILL_GST.md` | **The methodology** — source hierarchy, citation rules, answer workflow, update discipline | ✅ v1 ready |
| `law-library/acts/` | CGST / IGST / Cess Acts **as on 01-01-2026** (chapter-wise files) | ✅ LOADED 04-07-2026 |
| `law-library/rules/` | CGST Rules (19 chapters), IGST Rules, GSTAT Rules 2023 & (Procedure) 2025, Cess Rules — **as on 01-01-2026** | ✅ LOADED 04-07-2026 |
| `law-library/notifications/` | Rate + non-rate notifications, indexed. (Per-section NN tracker embedded in loaded Act/Rules text; full NN 11/12-2017-CT(R) texts still to load) | 🟡 partial (tracker only) |
| `law-library/circulars/` | CBIC circulars, indexed by number/topic | 🔴 to load |
| `returns/` | Return forms map, due-date calendar, entity filing tracker | 🟡 template ready |
| `cases/` | Litigation tracker — notices, replies, orders, appeals, deadlines | 🟡 template ready |
| `positions/` | Positions register — YOUR stance on recurring issues, with citations | 🟡 template ready |
| `telegram-bot/` | **Telegram enquiry bot** — ask law/rules questions from your phone; answers only from the law library, with citations (`telegram-bot/README.md` for setup) | ✅ v1 ready — needs library docs loaded |
| `recon/` | **GSTR-1 books-vs-portal reco** (Rules G1–G4) — match bill no / taxable / rate / GST amount, exception buckets with actions. Run before filing every R1. `python recon/gstr1_reco.py books.xlsx portal.xlsx out.xlsx` | ✅ v1 ready — tested |

## 2. Source documents (Drive)

*To be filled as documents are loaded. Pattern: one row per source file, with Drive ID.*

| Document | Version/as-amended date | Drive ID / link | Loaded |
|---|---|---|---|
| **GST Manual (Garg & Garg, 2nd ed.)** — CGST Act & Rules, IGST Act & Rules, Cess Act & Rules, GSTAT Rules 2023 + (Procedure) 2025, per-section NN/circular tracker | **01-01-2026** | `1zQQoAOMZrpsPuLxlTJlur3Hy3_uh-84z` (folder `GST LAW -LIBRARY`) | ✅ 04-07-2026 → 60+ md files under `law-library/` |
| Notification compilations — full texts of NN 11/2017 & 12/2017-CT(R) as amended (manpower-supply rate/exemptions) | — | — | ☐ next |
| Circular compilation | — | — | ☐ |
| UTGST Act (only if a matter needs it) | — | — | ☐ |

⚠️ The loaded text is a professional compilation, not the official Gazette — for
filings/litigation verify operative wording against CBIC. Anything amended
**after 01-01-2026** is not in the library; every answer for later periods must
carry that caveat.

**Official sources to download from:** cbic-gst.gov.in (Acts/Rules/Notifications/Circulars — "GST Law" section), gstcouncil.gov.in (Council decisions), gst.gov.in (portal advisories). Prefer the CBIC "updated/as-amended" PDFs which consolidate amendments.

## 3. Entities & registrations

*Fill in — needed for returns tracking and case context.*

| Entity | GSTIN | State | Scheme (regular/composition) | Notes |
|---|---|---|---|---|
| ISPL (Impressions Services) | — | (multi-state?) | — | pan-India manpower services — likely multiple GSTINs |

## 4. Open items

| # | Item | Status |
|---|---|---|
| 1 | Load law library — Acts & Rules ✅ done 04-07-2026 (GST Manual as on 01-01-2026). Remaining: full texts of NN 11/2017 & 12/2017-CT(R) as amended + key circulars — see `law-library/SOURCES_TO_LOAD.md` | 🟡 acts/rules DONE, NNs next |
| 2 | Fill entity/GSTIN table (§3) and returns calendar | 🔴 pending |
| 3 | Load pending cases/notices into `cases/CASE_TRACKER.md` | 🔴 pending |
| 4 | Record first positions on recurring issues (e.g. manpower supply valuation, RCM items) | 🔴 pending |
| 5 | Deploy Telegram bot (`telegram-bot/README.md`) — needs BotFather token + API key + a machine that stays on | 🟡 code ready |
| 6 | Run first live GSTR-1 reco (`recon/`) — needs current month's sales register + portal GSTR-1 export | 🟡 tool ready |
| 7 | **June-26 IRN pending: 367 docs, net ₹5.56 Cr, GST ₹98.3L not yet e-invoiced** (Drive `1KIZPBAtFif0N-GlLJHbWsjpPGDuzlMMj`, analyzed 04-07-2026). 17 docs already >30 days old (₹2.1L GST — IRP 30-day window risk, mostly SIGNIFY/Karnataka + ALTF CNs), 145 docs at 24–30 days (₹35.4L GST). Worklist issued; generate IRNs before filing June R1 | 🔴 URGENT |
| 8 | UNBS FY 2021-22 vendor ledger received — logged in `cases/CASE_TRACKER.md`; awaiting context (which notice/query?) | 🟡 awaiting Dinesh |

## 5. Update discipline

Same as the salary brain: **every document loaded, case moved, or position taken →
update §2/§3/§4 here in the same commit.** The brain is only as alive as its index.
