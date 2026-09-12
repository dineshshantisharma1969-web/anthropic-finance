# ISPL Bank Statement Tracker — client attribution

`clientlib.py` turns the tracker's raw transaction rows into day-wise client
collections for the "Clients" view of the daily bank-statement artifact.

## Why it exists

The tracker's `Party Name` column is blank on roughly a fifth of receipts —
the bank simply does not populate it for CMS collections, cheque clearing,
PFMS credits and several NEFT/RTGS formats. Those receipts were all landing in
a single "(Unidentified)" bucket worth **₹13.47cr**. `clientlib.py` reads the
payer out of the narration instead, which cuts the unattributed pile to
**₹34.20L (0.4%)**.

## What it does

- `from_narration(n)` — best-effort payer name from a bank narration.
  Handles CMS, NEFT, RTGS, IMPS, CLG, TRF, SGB, CHQ DEP, FT and `TRFR FROM:`
  formats. Returns `''` when the narration genuinely names nobody.
- `canonical(names)` — merges truncated bank spellings of one payer
  (`JONES LANG LASALLE PROPERT` → `JONES LANG LASALLE PROPERTY`).
- `load(path)` — deduped, rule-compliant client receipt rows.

## Two traps worth knowing

**Bank words appear inside real client names.** `THE HDFC SCHOOL GURGAON` is a
school, not a bank. So the extractor never cuts at the *first* bank word — it
strips only a bank descriptor that runs to the end of the string
(`… STATE BANK OF INDIA SBIN0003…`). Cutting at the first match turned that
school into a client called "THE".

**Short prefixes are not evidence.** `canonical()` only merges names of 10+
characters, so a stub like `THE` never gets folded into an unrelated longer
name.

## Inter-bank exclusions

Applies the same rules as the bank view — most importantly, a credit whose
narration contains the literal `*IMPRESSIONS SERV` (asterisk immediately
before) is an own-account self-transfer, not a client receipt. Do **not**
loosen this to "IMPRESSIONS SERV + a routing code": `IMPRESSIONS SERVICES` is
our own beneficiary name on every incoming NEFT, so the looser match wrongly
flags genuine client payments.

## Invariant

Day-wise client totals must tie exactly to bank-side receipts for every date.
As of 12-Sep-2026: ₹78.90cr on both sides, zero variance across all 43 days.
If a day ever differs by more than ₹1, something is wrong — investigate rather
than publish.
