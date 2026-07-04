# Law Library — Sources to Load (action needed from Dinesh)

> **Why this file exists:** the golden rule of this brain is that no legal text is
> written from AI memory — every provision must come from an official source
> document. The official sites (cbic-gst.gov.in, taxinformation.cbic.gov.in,
> indiacode.nic.in) **block access from outside India**, so Claude cannot download
> them directly (verified 04-07-2026: HTTP 403 on all three). The documents must be
> downloaded from India and handed to Claude.

## How to hand documents to Claude (either works)

1. **Google Drive** — create a folder (e.g. `gst-law-library`) and drop the PDFs
   there; then tell Claude *"load the GST law files from Drive"*. Files under
   ~10 MB each work best — if a PDF is bigger, split it by chapter.
2. **Direct upload** — attach the PDF in the chat (like the April salary file).

Claude then extracts the text to markdown under `law-library/`, indexes every
document with its version date in the INDEX files, and commits.

## Priority order (download the LATEST "updated/as-amended" version of each)

| # | Document | Where (open from India) |
|---|---|---|
| 1 | **CGST Act 2017** — updated version | cbic-gst.gov.in › GST Law › Acts (look for "CGST Act updated as on …" with the newest date) |
| 2 | **CGST Rules 2017** — Part A (Rules), updated | cbic-gst.gov.in › GST Law › Rules |
| 3 | **IGST Act 2017** — updated | same page as #1 |
| 4 | Rate notifications — NN 11/2017 & 12/2017-CT(R) as amended (services rates + exemptions — manpower supply lives here) | cbic-gst.gov.in › GST Law › Notifications |
| 5 | Non-rate notifications compilation (registration, returns, e-invoice) | same |
| 6 | Circulars relevant to open issues (start with any cited in notices you hold) | cbic-gst.gov.in › GST Law › Circulars |
| 7 | UTGST Act / Compensation Cess Act (only if needed) | same as #1 |

**Known-official direct links** (these were live per web search, but may be OLDER
compilations — always prefer the newest "updated" version listed on the site):

- [CGST Act updated 01-01-2022 (old.cbic.gov.in)](https://old.cbic.gov.in/resources/htdocs-cbec/gst/CGST%20Act,%202017%20as%20amended%20up%20to%2001.01.2022.pdf)
- [CGST Act updated 31-08-2021](https://cbic-gst.gov.in/pdf/CGST-Act-Updated-31082021.pdf)
- [CGST Rules Part A updated 01-06-2021](https://cbic-gst.gov.in/pdf/01062021-CGST-Rules-2017-Part-A-Rules.pdf)
- [CBIC Tax Information Portal — Acts](https://taxinformation.cbic.gov.in/content-page/explore-act/1000285/1000001)

⚠️ A 2021/2022 compilation is **missing 4+ years of amendments** (incl. Finance
Acts 2023–2026). Fine as a starting skeleton, but the amendments log in
`acts/INDEX.md` must flag it, and answers for recent periods must say the
library's version date.

## What happens after loading

Each document gets: a row in `GST_KNOWLEDGEBASE.md §2` (with Drive ID + version
date), a row in the relevant `INDEX.md`, and text under `law-library/…`. From
then on the Telegram bot and any Claude session answer from these files with
citations.
