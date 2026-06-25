# Addendum for `pf-salary-reconciliation` skill — M12 Zero-Basic Gate (verified 2026-06-25)

> Paste this section into `PF_SALARY_RECONCILIATION_SKILL_v4.md` (or via **Settings → Capabilities**).
> It documents the zero-basic gate exactly as applied, so the scheduled loop has the complete rule.

## M12 — Zero-Basic Gate (NET sacrosanct)

For every row whose **ORIGINAL `BASIC` == 0**:

1. **NET PAYABLE is sacrosanct.** Do not run earnings/PF/ESI rebuild rules to manufacture a net.
   If the original `NETPAYABLE` was 0, `REVISED_NET_PAYABLE` must stay **0**. If the original net was
   non-zero (e.g. arrears/allowance-only rows), it is preserved unchanged — never forced to 0.
2. **`REVISED_BASIC` and `REVISED_PF` must be 0** — *unless PF was actually deposited for that row.*
3. **ECR-PF exception (the one case rules still apply):** if `ECR_PF > 0` (PF genuinely deposited via
   the ECR challan, typical of **multi-site** employees who have BASIC=0 on this site's row but earn at
   another), the row **keeps the deposited PF**:
   - `REVISED_PF   == ECR_PF`
   - `REVISED_BASIC == ECR_PF / 0.12`  (back-solved wage base)
   - `REVISED_NET_PAYABLE` still follows rule 1 (stays 0 when original net was 0).
   These rows are tagged `MULTI_SITE_ZERO_PF` (or `COND2`). Zeroing them would understate real PF
   liability, so they are intentionally **not** flattened.

Rationale: a BASIC=0 row carries no own-site earnings, so the full reconstruction (12% Basic fix,
min-wage floor, ESI passes, projection caps) is skipped — except that PF actually filed in ECR must be
mirrored so the PF totals continue to tie to the challan.

## Verification gate (run every loop cycle)

`salary_reconciliation/verify_zero_basic_gate.py` enforces M12 across all monthly files and exits
non-zero on any breach. The loop should run it after the monthly rebuild:

```bash
python verify_zero_basic_gate.py "<folder with the 12 monthly xlsx>"
```

It flags three violation classes among BASIC=0 rows:

| Code | Meaning |
|---|---|
| **V1** | original NET == 0 but `REVISED_NET_PAYABLE` != 0  (net wrongly changed) |
| **V2** | `ECR_PF` == 0 but `REVISED_BASIC`/`REVISED_PF` != 0  (should have been zeroed) |
| **V3** | `ECR_PF` > 0 but `REVISED_PF` != `ECR_PF`  (deposited PF not mirrored) |

## Evidence — FY 2025-26, all 12 months PASS (2026-06-25)

- 5,710 rows had original BASIC = 0 across the 12 reconciled months.
- V1 = 0, V2 = 0, V3 = 0 → **PASS** on every month.
- 119 of those rows carried deposited PF (`ECR_PF > 0`): June 1, **November 49, December 69**.
  All 119 correctly keep `REVISED_PF == ECR_PF` and `REVISED_BASIC == ECR_PF/0.12`, with NET still 0.
- (Separately, 16 rows in Aug/Oct/Dec have non-zero revised NET — each had a non-zero *original* net,
  so M12 rule 1 preserves it; not a violation.)
