# PF-GST-Vault

Your PF / GST / Labour-Codes / Income-Tax **second brain**, structured as an Obsidian vault.

## How to open in Obsidian
1. Open Obsidian → **Open folder as vault** → select this `PF-GST-Vault` folder.
2. Recommended plugins (see `../docs` setup guide): **Dataview**, **Templater**, **Tag Wrangler**, **Obsidian Git**, **QuickAdd**.
3. With **Obsidian Git** installed, this vault auto-commits/pushes so it stays in sync across devices via the repo it lives in.

## Layout
| Folder | Purpose |
|---|---|
| `00-Inbox/` | Unsorted captures — new circulars, quick notes |
| `01-MOCs/` | Maps of Content — one hub note per domain (your entry points) |
| `02-PF/` | Provident Fund — scheme rules, reconciliation cases, circulars, wage-floor rules |
| `03-GST/` | GST — Act sections, circulars, notice replies, case log |
| `04-Labour-Codes-2020/` | Labour Codes 2020 |
| `05-Income-Tax/` | Income Tax |
| `06-Templates/` | Note templates (case / circular / provision / weekly log) |
| `07-Attachments/` | PDFs, screenshots, scanned notices |
| `08-Archive/` | Closed cases, superseded circulars |

## Conventions
- **Atomic notes** — one circular / section / case per note.
- **YAML frontmatter** on every note (`type`, `domain`, `status`, `tags`) so Dataview can query across the vault.
- **Nested tags** — `#domain/pf`, `#domain/gst`, `#type/case`, `#status/open`, etc.
- **MOCs are hubs, not folders** — link out from each MOC (or use Dataview) rather than browsing folders.

> Spreadsheets and PDFs (e.g. the ESI Washing Reallocation working set) live in Google Drive. They are represented here as **case notes that link to the Drive files**, so the vault stays lightweight and Obsidian-native while the source-of-truth workbooks stay in Drive.
