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

## Dedupe: normalise the reference before comparing

`_dedupe_key()` strips a trailing `-YYYY-MM-DD-<amount>` from the reference
segment of the Txn Key before comparing.

The importer sometimes writes the same receipt twice — once with a plain
reference and once with that suffix appended. The two rows then carry
different Txn Keys, so a raw Txn-Key dedupe keeps both and the receipt is
counted twice. Found 14-Sep-2026 when Dinesh spotted ITC Hotels showing
₹31.93L on 01-Sep against a bank credit of ₹15.97L. A ₹1.32L JLL credit into
KOTAK on 09-Sep had the same defect. Together they overstated collections by
₹17,28,248.96.

**Do not dedupe on (bank, date, amount).** Genuine separate receipts of equal
value exist and must all be kept — five ₹12,515 government credits on
08-Sep-2026, two Interglobe Air Transport pairs on 28-Aug-2026. Only a shared
underlying *reference* proves a duplicate.

### Also fixed at source (14-Sep-2026)

The suffix originates in the importer workflow `hqrLbu8oBQxIURU3`
("ISPL Bank Statement Loop (LIVE)"): the HDFC and KOTAK parsers build the
Reference No as `rawref-YYYY-MM-DD-amount`, and `Append To Tracker` uses
`appendOrUpdate` keyed on the Txn Key. When a receipt is re-imported after that
format was introduced, its key no longer matches the earlier clean-reference
row, so it is appended as a new row. The `normRefKey` that builds the Txn Key
(in the `Fix SBI Statement Dates` node — the last code node before the append)
now strips the same `-YYYY-MM-DD-amount` suffix and rebuilds every row's key, so
a re-import updates the existing row instead of duplicating it. This reporting
layer keeps its own normalisation as defence in depth — both layers agree.

## Files

- `clientlib.py` — payer attribution and dedupe (Python, used by the artifact refresh)
- `rebuild_bank.py` — bank-side day matrix for the artifact's `DATA` payload
- `daywise_core.js` — the same logic in JavaScript, mirrored into the n8n Code
  node of workflow `LcAhZwHuDdFW4FDf` ("ISPL — Collections Daywise by Client"),
  which rebuilds the Sheet's `<Month> <Year> - Collections Daywise` tab.
  Keep the two in sync; they are verified to agree to the paisa.
