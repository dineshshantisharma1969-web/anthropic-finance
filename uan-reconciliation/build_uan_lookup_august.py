import openpyxl, re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

def nc(v):
    if v is None: return ""
    s=str(v).strip()
    if s.endswith(".0"): s=s[:-2]
    return s
def nu(v):
    if v is None: return ""
    s=str(v).strip()
    if s.endswith(".0"): s=s[:-2]
    return re.sub(r"\s+","",s)

wb=openpyxl.load_workbook("aug_pf_ecr.xlsx",read_only=True,data_only=True)
recs=[]; blank_uan=0; total_rows=0
for sh in ("AUG_DELHI","AUG_DMART","AUG_STEAGE"):
    ws=wb[sh]; rows=list(ws.iter_rows(values_only=True)); hdr=rows[0]
    idx={str(h).strip().upper():i for i,h in enumerate(hdr) if h is not None}
    ci=idx["EMP CODE"]; ui=idx["UAN NO"]; ni=idx.get("NAME"); pi=idx.get("PF NO"); fhi=idx.get("F/H NAME")
    for r in rows[1:]:
        if r is None: continue
        code=nc(r[ci]); 
        if not code: continue
        total_rows+=1
        uan=nu(r[ui])
        if not uan: blank_uan+=1; continue
        name=str(r[ni]).strip() if ni is not None and r[ni] is not None else ""
        fh=str(r[fhi]).strip() if fhi is not None and r[fhi] is not None else ""
        pfno=nc(r[pi]) if pi is not None else ""
        recs.append((code,uan,name,fh,pfno))

# dedupe by code, detect conflicts
seen={}; final=[]; conflicts=0
for code,uan,name,fh,pfno in recs:
    if code in seen:
        if seen[code]!=uan: conflicts+=1
        continue
    seen[code]=uan; final.append((code,uan,name,fh,pfno))
badlen=sum(1 for c,u,n,f,p in final if len(u)!=12)
print(f"AUG filed rows={total_rows} blank_UAN(new joiners)={blank_uan} unique EMPCODE->UAN={len(final)} conflicts={conflicts} nonstd_UAN_len={badlen}")

# build xlsx (same layout as before)
wbn=Workbook(); ws=wbn.active; ws.title="UAN_LOOKUP"
ws.append(["EMPCODE","UAN NO","NAME","F/H NAME","PF NO"])
for c in ws[1]: c.font=Font(bold=True,color="FFFFFF"); c.fill=PatternFill("solid",fgColor="1F4E78")
for row in final: ws.append(list(row))
for col in ("A","B","E"):
    for cell in ws[col]: cell.number_format="@"
ws.column_dimensions["A"].width=14; ws.column_dimensions["B"].width=16
ws.column_dimensions["C"].width=28; ws.column_dimensions["D"].width=26; ws.column_dimensions["E"].width=12
ws.freeze_panes="A2"
h=wbn.create_sheet("HOW_TO_USE")
for row in [
 ["AUGUST 2026 — UAN LOOKUP (from PF ECR)"],
 ["Source PF ECR file: ECR_PF_AUGUST2026_BUILD.xlsx (sheets AUG_DELHI + AUG_DMART + AUG_STEAGE)"],
 [f"Unique employees (EMPCODE -> UAN): {len(final)}   |   New joiners without a UAN yet (excluded): {blank_uan}"],
 [""],
 ["PURPOSE"],
 ["Fill the August salary sheet's 'UAN NO' where blank, using the UAN filed in the PF ECR, matched on EMPCODE."],
 ["Existing UANs are left unchanged. New joiners with no UAN in the ECR cannot be filled (they have none yet)."],
 [""],
 ["HOW TO APPLY (in the salary sheet)"],
 ["1. Copy the 'UAN_LOOKUP' sheet into the salary workbook (or keep this file open alongside)."],
 ["2. Helper column next to UAN NO (adjust cell refs):"],
 ["   =IF(TRIM(<UAN NO cell>)<>\"\", <UAN NO cell>, IFERROR(VLOOKUP(TEXT(<EMPCODE cell>,\"0\"), UAN_LOOKUP!$A:$B, 2, FALSE), \"\"))"],
 ["3. Paste the helper back onto UAN NO as values; delete the helper."],
 [""],
 ["NOTES"],
 ["- EMPCODE and UAN NO stored as TEXT to protect leading digits / avoid scientific notation."],
 ["- Every EMPCODE in this list maps to exactly one 12-digit UAN (no duplicates, no blanks)."],
]: h.append(row)
h["A1"].font=Font(bold=True,size=13); h["A5"].font=Font(bold=True); h["A9"].font=Font(bold=True); h["A15"].font=Font(bold=True)
h.column_dimensions["A"].width=115
wbn.save("August_2026_UAN_LOOKUP.xlsx")
print("wrote August_2026_UAN_LOOKUP.xlsx")
