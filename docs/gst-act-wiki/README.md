# GST Act Wiki — CGST Act, 2017 (Section-wise Reference)

A practitioner-oriented, section-wise reference to the **Central Goods and Services Tax Act, 2017**, written for day-to-day use in accounts, compliance and litigation tracking at a manpower/services company. Companion pages cover the IGST Act, the Schedules, and the rate structure.

> **Can we legally put the GST Act in our wiki?** Yes. Acts of Parliament and State Legislatures are "Government works", and Section 52(1)(q) of the Copyright Act, 1957 expressly permits the reproduction or publication of any Act of a Legislature (including with commentary). Reproducing and summarising the CGST Act in an internal or public wiki is lawful.

> **Disclaimer:** These pages are working summaries, not the authoritative text. For the exact statutory wording always check the official sources below. Position stated is as amended up to the Finance Act, 2025 (to the best of our knowledge); verify recent amendments before relying on any provision.

## Official sources (authoritative text)

- CBIC — GST Acts and Rules: https://cbic-gst.gov.in/gst-acts.html
- India Code (CGST Act, 2017): https://www.indiacode.nic.in/handle/123456789/2278
- GST Council — rate notifications and circulars: https://gstcouncil.gov.in
- GST portal: https://www.gst.gov.in

## Pages in this wiki

| Page | Coverage | Sections |
|---|---|---|
| [1. Basics, Levy & Supply](gst-act-01-basics-levy-supply.md) | Preliminary, definitions, administration, levy, composition, RCM, exemption, time & value of supply | 1–15 |
| [2. Input Tax Credit](gst-act-02-input-tax-credit.md) | Eligibility, conditions, blocked credits, ISD, job work | 16–21 |
| [3. Registration](gst-act-03-registration.md) | Threshold, compulsory registration, amendment, cancellation, revocation | 22–30 |
| [4. Invoicing, Accounts & Returns](gst-act-04-invoicing-accounts-returns.md) | Tax invoice, credit/debit notes, e-invoicing, accounts, GSTR returns | 31–48 |
| [5. Payment, TDS/TCS & Refunds](gst-act-05-payment-refunds.md) | Electronic ledgers, interest, GST TDS (s.51), TCS (s.52), refunds | 49–58 |
| [6. Assessment, Audit, Demands & Recovery](gst-act-06-assessment-audit-demands.md) | Self/provisional/best-judgment assessment, audit, s.73/74/74A demands, recovery | 59–84 |
| [7. Appeals, Offences & Miscellaneous](gst-act-07-appeals-offences-misc.md) | Liability in special cases, advance ruling, appeals, GSTAT, penalties, transitional, misc | 85–174 |
| [8. Schedules & Rate Structure](gst-act-08-schedules-and-rates.md) | Schedules I–III, rate slabs, manpower-supply specifics | Sch. I–III |

## How to move these pages into the GitHub Wiki

The GitHub Wiki is a separate git repository. From your own machine:

```bash
git clone https://github.com/dineshshantisharma1969-web/anthropic-finance.wiki.git
cp docs/gst-act-wiki/*.md anthropic-finance.wiki/
cd anthropic-finance.wiki && git add -A && git commit -m "Add GST Act pages" && git push
```

Or simply create each page in the Wiki UI and paste the markdown. Internal links use relative `.md` filenames, which GitHub Wiki resolves if the pages keep the same names.

## Quick relevance map for ISPL (manpower / security / facility services)

- **Rate:** Supply of manpower, security and housekeeping services — **18% (SAC 9985)**. Security services (by a non-body-corporate to a registered person) fall under **RCM** — see [Page 1](gst-act-01-basics-levy-supply.md).
- **GST TDS (Section 51):** Government departments/PSUs deduct 2% on contracts > ₹2.5 lakh — reconcile with GSTR-7 credits, see [Page 5](gst-act-05-payment-refunds.md).
- **ITC hygiene:** Section 16(2)(aa)/(ba) — credit only if it appears in GSTR-2B; vendor follow-up matters, see [Page 2](gst-act-02-input-tax-credit.md).
- **Notices:** Time limits for demands now unified under Section 74A from FY 2024-25 — see [Page 6](gst-act-06-assessment-audit-demands.md).
