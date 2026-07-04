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
| `law-library/acts/` | CGST / IGST / UTGST / SGST / Compensation Cess Acts, as amended | 🔴 to load |
| `law-library/rules/` | CGST Rules 2017 (as amended), other rules | 🔴 to load |
| `law-library/notifications/` | Rate + non-rate notifications, indexed | 🔴 to load |
| `law-library/circulars/` | CBIC circulars, indexed by number/topic | 🔴 to load |
| `returns/` | Return forms map, due-date calendar, entity filing tracker | 🟡 template ready |
| `cases/` | Litigation tracker — notices, replies, orders, appeals, deadlines | 🟡 template ready |
| `positions/` | Positions register — YOUR stance on recurring issues, with citations | 🟡 template ready |
| `telegram-bot/` | **Telegram enquiry bot** — ask law/rules questions from your phone; answers only from the law library, with citations (`telegram-bot/README.md` for setup) | ✅ v1 ready — needs library docs loaded |

## 2. Source documents (Drive)

*To be filled as documents are loaded. Pattern: one row per source file, with Drive ID.*

| Document | Version/as-amended date | Drive ID / link | Loaded |
|---|---|---|---|
| CGST Act 2017 (updated) | — | — | ☐ |
| IGST Act 2017 (updated) | — | — | ☐ |
| CGST Rules 2017 (updated) | — | — | ☐ |
| Notification compilations (rate/non-rate) | — | — | ☐ |
| Circular compilation | — | — | ☐ |

**Official sources to download from:** cbic-gst.gov.in (Acts/Rules/Notifications/Circulars — "GST Law" section), gstcouncil.gov.in (Council decisions), gst.gov.in (portal advisories). Prefer the CBIC "updated/as-amended" PDFs which consolidate amendments.

## 3. Entities & registrations

*Fill in — needed for returns tracking and case context.*

| Entity | GSTIN | State | Scheme (regular/composition) | Notes |
|---|---|---|---|---|
| ISPL (Impressions Services) | — | (multi-state?) | — | pan-India manpower services — likely multiple GSTINs |

## 4. Open items

| # | Item | Status |
|---|---|---|
| 1 | Load law library (Acts → Rules → notification/circular indexes) | 🔴 IN PROGRESS |
| 2 | Fill entity/GSTIN table (§3) and returns calendar | 🔴 pending |
| 3 | Load pending cases/notices into `cases/CASE_TRACKER.md` | 🔴 pending |
| 4 | Record first positions on recurring issues (e.g. manpower supply valuation, RCM items) | 🔴 pending |
| 5 | Deploy Telegram bot (`telegram-bot/README.md`) — needs BotFather token + API key + a machine that stays on | 🟡 code ready |

## 5. Update discipline

Same as the salary brain: **every document loaded, case moved, or position taken →
update §2/§3/§4 here in the same commit.** The brain is only as alive as its index.
