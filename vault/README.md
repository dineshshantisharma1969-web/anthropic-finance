# 🧠 ISPL Compliance Second Brain

A queryable knowledge base for **Salary/PF/ESI**, **GST**, and **Income Tax** compliance at
ISPL (Impressions Services). Built as plain Markdown so it works three ways at once:

- **Obsidian** — browse, link, graph-view, edit by hand.
- **Claude Code** — I read these notes to answer your queries with citations.
- **Pinecone / RAG** (optional, later) — consistent frontmatter makes vector retrieval work.

---

## The one rule that makes this work: folders encode *stability*, not *topic*

Topic (GST, PF, salary) lives in **frontmatter `domain` + tags + links** — never in the folder
name. Folders encode an item's **lifecycle stage**, because that is what is hard to change later.

| Folder | What goes here | Edited? |
|---|---|---|
| `00-Inbox/` | Raw captures — pasted notice text, unsorted snippets | Freely; emptied as sorted |
| `10-Law/` | Verbatim statutory source (GST, Income-Tax, PF-ESI) | **Never** — only superseded |
| `20-Rules/` | ISPL's interpretation & working rules (Case A/B, 50% wage code…) | Versioned via `status` |
| `30-Notices/` | One dated note per live GST / IT notice | Appended as it progresses |
| `40-Workings/` | Recon runs, analyses, computed results — dated | Immutable once done |
| `90-Maps/` | Index + one MOC (Map of Content) per domain | Living |
| `_templates/` | Note templates with YAML baked in | — |
| `_attachments/` | Images, PDFs, embedded files | — |

## Frontmatter is the contract (matters more than the tree)

Every note starts with YAML. You can restructure folders anytime; inconsistent frontmatter is
painful to backfill. Minimum fields:

```yaml
type:            # law | rule | notice | working
domain:          # gst | income-tax | pf | esi | salary
ref:             # section / para / case-rule / notice no.
title:
effective_from:  # YYYY-MM-DD
effective_to:    # blank = still in force
status:          # active | superseded | draft
supersedes:      # [[note]] this replaces  (blank if none)
superseded_by:   # [[note]] that replaces this  (blank if current)
source:          # where the text/number came from
tags: []
created:         # YYYY-MM-DD
```

## Two more habits

- **One note = one atomic unit.** One section, one para, one case rule, one notice, one recon
  run. Not "GST — everything." Atomic notes link cleanly and retrieve precisely.
- **Never delete law or rules — supersede them.** Flip `status: superseded`, set
  `superseded_by:`, and keep the old note. That history is your audit defence when a notice
  concerns an earlier period. `effective_from`/`effective_to` let point-in-time queries pull
  the rule *as it stood then*.

---

## How to query it

Just ask me (Claude Code), e.g.:
- *"What's our 50% wage-code rule and how do day-rated employees get treated?"*
- *"Show me the PF reconciliation result for FY25-26 and how it ties to the ECR."*
- *"Draft a reply to this ASMT-10"* → paste it into `00-Inbox/`, I'll pull the relevant
  `10-Law/GST` + `20-Rules` notes and draft against them.

I read the matching notes and answer with citations to the exact note. No Pinecone needed to
start — that's an optional layer for when the vault grows large.

See **[[90-Maps/index]]** to navigate.
