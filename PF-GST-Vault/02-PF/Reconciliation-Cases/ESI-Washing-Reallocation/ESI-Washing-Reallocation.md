---
type: case
domain: pf
status: watch
opened: 2026-07-11
deadline:
source: Google Drive — ESI_WASHING_REALLOCATED
drive_folder: https://drive.google.com/drive/folders/1phx-Pv7qLvWgmyZlGUsZdhCPTNhz35ui
tags: [domain/pf, domain/esi, type/case, status/watch, fy/2025-26, m13]
---

# ESI Washing Reallocation — PF/ESI M13 FINAL Reconciliation (FY2025-26)

> [!info] Source of truth
> The workbooks below live in Google Drive folder **[ESI_WASHING_REALLOCATED](https://drive.google.com/drive/folders/1phx-Pv7qLvWgmyZlGUsZdhCPTNhz35ui)**. This note is the Obsidian index — open it to reach any file, then edit the workbook in Drive. Backups (`*.bak.xlsx`) and the raw download zip are kept but collapsed at the bottom.

Linked from [[MOC-PF]].

## Summary
Full-year PF/ESI reconciliation for FY2025-26 across all 12 months, run under **Rule M13** (PF 12% on BASIC+DA, revised block back-solved from ECR while holding NET). Includes the ESI reallocation ("washing") pack, monthly ESI/WageCode recovery worklists, ESI eligibility/exemption/enrolment audits, and the finalised M13 workbooks per month.

Per `FINAL_REPORT.md` the run is a **HARDPASS**: NET drift zero on every row and total, `REVISED_PF == ECR_PF` (0 drift), `REVISED_ESIC == ESIC AS PER FUTURE` (0 drift). **2 exceptions remain** (DA alone exceeds ECR_PF/0.12, basic clamped) — see `PF_M13_Exceptions_Review.xlsx`. Status is `watch` until those 2 are cleared.

## Facts (from FINAL_REPORT.md)
- Rule M13: `ECR_PF > 0 → REVISED_BASIC = ECR/0.12 − DA` (plug to attendance allowance; GROSS/PF/NET held).
- `ECR_PF = 0 → (BASIC+DA)*FULL_MONTH/ADJ_WORKING_DAYS > 15000` via day reduction then REVISED_BASIC lift; absorbed by attendance allowance, else OTHER_DEDUCTION (GROSS & TOTAL_DED rise, NET unchanged).
- 12 months, ~18.6k–20.3k active rows/month. Originals untouched; change logs per month in `_change_logs/`.

## Next Step
- [ ] Clear the 2 remaining M13 exceptions (Sep + Feb) in `PF_M13_Exceptions_Review.xlsx`.
- [ ] Confirm ESI reallocation totals in `ESI_Reallocation_Summary_FINAL_v2.xlsx` tie to `PF_ESI_Reco_Summary_FY2025-26`.

---

## Reports & Summaries
- [FINAL_REPORT.md](https://drive.google.com/file/d/16-uOYOztJDGcMjiRj9dp_oR_ukuhyxHY/view) — M13 run report (invariants, per-month table)
- [PF_ESI_Reco_Summary_FY2025-26 (Sheet)](https://docs.google.com/spreadsheets/d/13dJywDQRXfGW8EZdCOc_2KvnX3Kp4a8wCafIRBEyAr0/edit)
- [PF_ESI_Reco_Summary_FY2025-26110726.xlsx](https://drive.google.com/file/d/12ILIGf0VSCR9ZDk9XaG3zNUcD9KbJ6pt/view)
- [PIVOT_12M_Summary_RevisedBlock_FY2025-26 (Sheet)](https://docs.google.com/spreadsheets/d/1x2FWQC_ja6-v3vo63P3_zTtWaic48WHk6u0xsBYm7Ug/edit)
- [Earnings_Deductions_Summary_FY2025-26 (Sheet)](https://docs.google.com/spreadsheets/d/1KfmHGRDF0mjOeggTmtnuHQn9215ZunvKGhCmCxhnydI/edit)
- [Monthly_Salary_Deductions_Summary_FY2025-26 (Sheet)](https://docs.google.com/spreadsheets/d/1n2Y2bxd7zMtKodPOEeWeFfaZljGYmx18uMUFCpe9ZIU/edit)

## ESI Reallocation ("Washing") Core
- [ESI_Reallocation_Summary_FINAL_v2.xlsx](https://drive.google.com/file/d/1IuQTNYsxhVfdrjrsgpPxTdvbu1McP9q7/view) ← latest
- [ESI_Reallocation_Summary_CORRECTED.xlsx](https://drive.google.com/file/d/19r5XAg-zWnx04qjTGDjsA-Ss0JD6mxV5/view)
- [ESI_Reallocation_Summary.xlsx](https://drive.google.com/file/d/10ufYQZD95yUd48b7J00HRtSlX4DRSL7A/view)

## ESI Audits & Eligibility
- [FY2526_ESI_Eligible_Monthwise_List.xlsx](https://drive.google.com/file/d/1QJyy9e33O23oZ9_B-UpJsZ6jbdR2EpBy/view)
- [FY2526_ESI_Enrollment_Audit.xlsx](https://drive.google.com/file/d/1h-j-FQTsLYk9Ucvh1dWdMkmjNQhcJqwo/view)
- [FY2526_ESI_Exemption_Audit.xlsx](https://drive.google.com/file/d/1qodkA9VEpmP99pfai5_g3j2ZlaKW4666/view)

## Monthly ESI / WageCode Recovery Worklists
- [April25](https://drive.google.com/file/d/1yMMqYr_i9cSVCZKOq0tABAx3pkAz8Z3s/view) ·
  [May25](https://drive.google.com/file/d/1QDivMCwzYPaEroymo4TnvhPEwzRgZdJC/view) ·
  [Jun25](https://drive.google.com/file/d/1QNGTYoUzUjoGbGHlpQ5lGXF2LRxOCyP5/view) ·
  [Jul25](https://drive.google.com/file/d/1OIWNSZY4MUaHvxnHNJ63Nf3flMXwORst/view) ·
  [Aug25](https://drive.google.com/file/d/12UMGOylh4I0SBVmRouZM3Cpb3Q2nkJCV/view) ·
  [Sep25](https://drive.google.com/file/d/1DYcCxYgpoPTH619Rd35cxqcHVslsFCF4/view)
- [Oct25](https://drive.google.com/file/d/1fSIqJWQODEJOrmH3DhjHvgzRs4zbKm7l/view) ·
  [Nov25](https://drive.google.com/file/d/1lkCchV4ULTkZHO6c7M2PrcOtPmEHvWMj/view) ·
  [Dec25](https://drive.google.com/file/d/1YUVzdcyxsk8dM03FK3W0YtDZBfkGAsOh/view) ·
  [Jan26](https://drive.google.com/file/d/1_5_0qfciTEYF3kofyMYseAZ6PcvLOJCt/view) ·
  [Feb26](https://drive.google.com/file/d/1SUsz05jAp7WaaQuzeEu9veFgU6KvTSwK/view) ·
  [Mar26](https://drive.google.com/file/d/1CNZEUXdbkgZ3imQMIVUSc_Cpldp-VoQB/view)

## WageCode Restructuring Packs
- [Dec25_Mar26_WAGECODE_50PCT_PACK_v2.xlsx](https://drive.google.com/file/d/1wN0dQ_35sVa6TjMgtDNP2JkekIi37U2q/view) ← latest
- [Dec25_Mar26_WAGECODE_50PCT_PACK.xlsx](https://drive.google.com/file/d/1_5PO4MwzbFwxiaVwy_VxMMzD3jp32mis/view)
- [JLL_WageCode_Restructuring_Annexure.xlsx](https://drive.google.com/file/d/1yAPui0Gr6o9WRrHe4Hw1k_MiRso8miLM/view)

## PF Reconciliation & ECR
- [ECR_PF_FORMAT_Monthwise_Merged_FY2025-26.xlsx](https://drive.google.com/file/d/18RUAZDZ-Jh-q2lhx2XLZTNfpOwAy2Asj/view)
- [ECR_PF_Monthly_Summary_FY2025-26.xlsx](https://drive.google.com/file/d/1OvZxBAhE_D7WtwJytvM57v_GOQstNK3n/view)
- [PF_Challan_vs_Reco_Comparison_FY2025-26.xlsx](https://drive.google.com/file/d/1eB87-V06Z3don89RM3Vk70QiC3i0LF1S/view)
- [PF_EE_Monthwise_Merged_vs_ECR_FY202526.xlsx](https://drive.google.com/file/d/1Wb4YJXRjDwifTAWQbJm8arBexC0gIrbl/view)
- [PF_ECR_vs_Salary_Rowwise_Reco_FY202526.xlsx](https://drive.google.com/file/d/1uFISkI-99BB94DDSfX0rbsZvG0mFuo05/view)
- [PF_M13_Exceptions_Review.xlsx](https://drive.google.com/file/d/1DEX3yEn7iK4WsY6I7_ihMBKC8DBmLjYi/view) ← 2 remaining exceptions
- [Fix_RevisedPF_M13_Apply_Report.xlsx](https://drive.google.com/file/d/1S6HeyUEwN0S3SvXJ2Lhq_gvhly7TiGmg/view)
- [Fix_RevisedPF_M13_Verification.xlsx](https://drive.google.com/file/d/1PaZSQSkiSI4DPzdhsfR74Q_51aiQyTaI/view)
- [Fix_RevisedPF_M13_DryRun_Report.xlsx](https://drive.google.com/file/d/1zrniuvIgA5eApYeg6UuyjjxpOFIXNtWU/view)
- [EPF Summary 25-26ANUJ.xlsx](https://drive.google.com/file/d/1lyB9R4yHnhPGeBwLkZ7DAMLovzFN_n4o/view)

## Salary Source
- [Salary_as_per_Max_SA_consolidated_SUMMARY.xlsx](https://drive.google.com/file/d/1dponOy36aZqEKW6KXnhpIdVlbq7YpwoP/view)
- [salary as per max.xlsx](https://drive.google.com/file/d/1ljY5N40azq7_QRedKQhdXRM4UxG3Y1h-/view)

## M13 FINAL — Monthly Workbooks (current)
- [April_M13_FINAL.xlsx](https://drive.google.com/file/d/1V5b1ageGYpK55-D0XzJUrbyfPtWeuKCY/view) ·
  [May_M13_FINAL.xlsx](https://drive.google.com/file/d/1l6lRRBE1iNY6SvhFwaZMiPMQLOiJS5eI/view) ·
  [June_M13_FINAL.xlsx](https://drive.google.com/file/d/1lJ99t4J2dLJUEx0q2i6aRV_whjNAFCLo/view)
  ([June PF-ECR-CORRECTED, Sheet](https://docs.google.com/spreadsheets/d/1Imzc2Vql3B48PWz4HKYf6IQY5cIJy6IeaUlWS_QBYjQ/edit)) ·
  [July_M13_FINAL.xlsx](https://drive.google.com/file/d/1DiHqqiBG8Gmcm_CxkqaSxWWrc9fodekz/view)
- [August_M13_FINAL.xlsx](https://drive.google.com/file/d/1oyRVn4r_HHAV9BQON5uBQKNqaCLEO7rZ/view) ·
  [September_M13_FINAL.xlsx](https://drive.google.com/file/d/1xYMScVeTxGoReMFiOzVT39EJPR0vB9fj/view) ·
  [October_M13_FINAL.xlsx](https://drive.google.com/file/d/1jq3QQohXyzSVGUeFaB3WTmIUUkG9hFTh/view) ·
  [November_M13_FINAL.xlsx](https://drive.google.com/file/d/12MpmgDKjctTWbXibLn5eDHXd7oC5XyVb/view)
- [December_M13_FINAL.xlsx](https://drive.google.com/file/d/10rL7LJz3G7C0MPQXroFj8qHfotZ2Hq_D/view) ·
  [January_M13_FINAL.xlsx](https://drive.google.com/file/d/1h9S0QmYNcCi2u83-vyLqB-tqHMsGT2xd/view) ·
  [February_M13_FINAL.xlsx](https://drive.google.com/file/d/1fGrhc7e9aAT4SwhF1QaUCdI9qXEKkIPX/view) ·
  [March_M13_FINAL.xlsx](https://drive.google.com/file/d/1sRpkQ1CscrIbLAMxjghCavod1k0Lswjh/view)

---

## Backups & Archives (superseded — kept for audit trail)

> [!note]- Pre-fix `.bak` snapshots and raw download zip (click to expand)
> **M13 `.preecrpffix.bak`:**
> [April](https://drive.google.com/file/d/1sK2kl95Kc8299NRhAq9P30KNAGV7DL1n/view) ·
> [May](https://drive.google.com/file/d/1EBz0N1XVn3AuTHSbvidXczL6gBEN8Dwa/view) ·
> [June](https://drive.google.com/file/d/1YNtFCtU3sBMbjMZpktWsIMFOZgC5U-uz/view) ·
> [July](https://drive.google.com/file/d/1Fipkw9lOMzIXp5l_j-wc3dfNS664j21t/view) ·
> [August](https://drive.google.com/file/d/1r_xS21PVhrG-CGbhL0ZntsobsZvITnMi/view) ·
> [September](https://drive.google.com/file/d/126Lszs8Yc2egMv9FCsMf7ceXZdB7nSuB/view) ·
> [October](https://drive.google.com/file/d/1T4zXIfqf6Rvond55TZqcfzNJ5ADBxMr-/view) ·
> [November](https://drive.google.com/file/d/1nEYsT2nyd8xAwFZYueN3Yy_WCZM86AAx/view) ·
> [December](https://drive.google.com/file/d/1plSjaG2mPw0klJI1xosr1Q9rp0GJssiN/view) ·
> [January](https://drive.google.com/file/d/1uPky_pFL13wrO66B6M5FEMoX6jFLmr22/view) ·
> [February](https://drive.google.com/file/d/1MbumWvc0BKfQyjlYTapdgUxAckf2vt94/view) ·
> [March](https://drive.google.com/file/d/16XuvKtu4KpUyX6trimCsNbbIbgQoaiAH/view)
>
> **M13 `.prestrayfix.bak`:** [January](https://drive.google.com/file/d/1RFsRCr7Cs1Dr0HFrUD-eeWSclR6A5_H5/view) · [February](https://drive.google.com/file/d/1tJxbl2oqkoE26MT1oJA0QyOyxTgxsDOy/view)
>
> **PF_EE reco backups:** [.prebofix.bak](https://drive.google.com/file/d/1vOgwMsiX8BGsw2_Sxz0Rs2XLsqsjh2SQ/view) · [.preECRfix.bak](https://drive.google.com/file/d/1ISx5PqUq8nx1x97kHxro9iOyWSPjbzT5/view)
>
> **Raw download:** [drive-download-20260702...zip](https://drive.google.com/file/d/1fVu_0TKrpL0pLSNt-_zWUZc1qsrqGr_4/view) (~332 MB)
