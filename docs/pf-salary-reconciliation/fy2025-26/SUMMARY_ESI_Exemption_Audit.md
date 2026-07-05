# ESI Exemption Audit — validity of every ESI exemption, all 12 months FY25-26

Parallel to the PF exemption audit. For every employee with **NO ESI contributed**
(exempt), verify the exemption is lawful. ESI exemption is valid only if full-month
gross **> ₹21,000** (the ESI wage ceiling). Split each month's exempt population:
- **VALID** — full-month gross > ₹21,000 (correctly exempt)
- **INVALID** — full-month gross ≤ ₹21,000 (wrongly exempt → must enrol)

## Result — 87% of exemptions valid; 12.7% are wrongly exempt

| Month | Total ESI-exempt | VALID (>21k) | INVALID — must enrol | Invalid exposure 4%/mo (₹) | Borderline (21k–23.1k) |
|---|--:|--:|--:|--:|--:|
| Apr-25 | 3,062 | 2,280 | 782 | 3,20,027 | 543 |
| May-25 | 2,474 | 2,140 | 334 | 1,41,498 | 479 |
| Jun-25 | 2,433 | 2,199 | 234 | 84,492 | 465 |
| Jul-25 | 2,497 | 2,246 | 251 | 74,143 | 418 |
| Aug-25 | 2,557 | 2,235 | 322 | 84,845 | 455 |
| Sep-25 | 2,471 | 2,285 | 186 | 44,213 | 488 |
| Oct-25 | 2,896 | 2,447 | 449 | 70,780 | 395 |
| Nov-25 | 2,749 | 2,393 | 356 | 85,899 | 501 |
| Dec-25 | 2,939 | 2,619 | 320 | 72,460 | 504 |
| Jan-26 | 2,864 | 2,583 | 281 | 1,03,033 | 590 |
| Feb-26 | 2,872 | 2,582 | 290 | 1,18,167 | 601 |
| Mar-26 | 2,924 | 2,579 | 345 | 1,43,114 | 411 |
| **TOTAL (row-instances)** | **32,738** | **28,588 (87.3%)** | **4,150 (12.7%)** | | ~500/mo |

## Reading it
- **Every month, ~87% of ESI exemptions are lawful** (gross genuinely > ₹21,000).
- The **INVALID 12.7%** are the exact rows of the ESI *enrollment* audit — same
  people, viewed as "wrongly exempt." 4,150 row-instances / 2,793 distinct
  employees / **284 persistent (≥3 months)** — enrol those first.
- **BORDERLINE (~500/month, gross ₹21,000–23,100)**: validly exempt today, but any
  increment or a wage-code restructuring (which raises Basic+DA, not gross — so
  usually safe, but arrears/OT can push gross down and these flip to eligible).
  Watch this band whenever wages are revised.

## Contrast with the PF exemption audit
PF exemption audit → **0 wrongly-exempt** (all part-month artifacts). ESI exemption
audit → **12.7% wrongly exempt** — a real, recurring compliance gap. ESI needs
active enrollment management; PF is clean.

Working file: `docs/pf-salary-reconciliation/fy2025-26/FY2526_ESI_Exemption_Audit.xlsx`
(EXEMPTION_AUDIT tab — the validity split per month). The invalid (enrol-now) list
with names/ESIC/UAN is in `FY2526_ESI_Enrollment_Audit.xlsx`.
