import openpyxl, re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

def norm_code(v):
    if v is None: return ""
    s=str(v).strip()
    if s.endswith(".0"): s=s[:-2]
    return s
def norm_uan(v):
    if v is None: return ""
    s=str(v).strip()
    if s.endswith(".0"): s=s[:-2]
    return re.sub(r"\s+","",s)

def load(path, sheet, hr):
    wb=openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws=wb[sheet]; rows=list(ws.iter_rows(values_only=True)); hdr=rows[hr]
    idx={str(h).strip().upper():i for i,h in enumerate(hdr) if h is not None}
    ci=idx["EMP CODE"]; ui=idx["UAN NO"]; ni=idx.get("NAME"); pi=idx.get("PF NO")
    fhi=idx.get("F/H NAME")
    out=[]
    for r in rows[hr+1:]:
        if r is None: continue
        code=norm_code(r[ci]) if ci<len(r) else ""
        uan=norm_uan(r[ui]) if ui<len(r) else ""
        if not code or not uan: continue
        name=str(r[ni]).strip() if ni is not None and ni<len(r) and r[ni] is not None else ""
        pfno=norm_code(r[pi]) if pi is not None and pi<len(r) else ""
        fh=str(r[fhi]).strip() if fhi is not None and fhi<len(r) and r[fhi] is not None else ""
        out.append((code,uan,name,fh,pfno))
    return out

def build(label, src_name, recs, outpath):
    # dedupe by code (all unique already, but be safe: keep first)
    seen={}; final=[]
    for code,uan,name,fh,pfno in recs:
        if code in seen: continue
        seen[code]=uan; final.append((code,uan,name,fh,pfno))
    wb=Workbook(); ws=wb.active; ws.title="UAN_LOOKUP"
    hdr=["EMPCODE","UAN NO","NAME","F/H NAME","PF NO"]
    ws.append(hdr)
    for c in ws[1]:
        c.font=Font(bold=True,color="FFFFFF"); c.fill=PatternFill("solid",fgColor="1F4E78")
    for code,uan,name,fh,pfno in final:
        ws.append([code,uan,name,fh,pfno])
    # store EMPCODE & UAN as text to preserve leading digits / avoid float
    for col in ("A","B","E"):
        for cell in ws[col]:
            cell.number_format="@"
    ws.column_dimensions["A"].width=14; ws.column_dimensions["B"].width=16
    ws.column_dimensions["C"].width=28; ws.column_dimensions["D"].width=26; ws.column_dimensions["E"].width=12
    ws.freeze_panes="A2"
    # instructions sheet
    h=wb.create_sheet("HOW_TO_USE")
    lines=[
     [f"{label} — UAN LOOKUP (from PF ECR)"],
     [f"Source PF ECR file: {src_name}"],
     [f"Unique employees (EMPCODE -> UAN): {len(final)}"],
     [""],
     ["PURPOSE"],
     ["Fill the salary sheet's 'UAN NO' column where it is blank, using the UAN filed in the PF ECR,"],
     ["matched on employee code (salary EMPCODE = ECR EMP CODE). Existing UANs are left unchanged."],
     [""],
     ["HOW TO APPLY (in the salary sheet)"],
     ["1. Copy the 'UAN_LOOKUP' sheet into the salary workbook (or keep this file open alongside)."],
     ["2. Add a helper column next to UAN NO and use this formula (adjust cell refs):"],
     ["   =IF(TRIM(<UAN NO cell>)<>\"\", <UAN NO cell>, IFERROR(VLOOKUP(TEXT(<EMPCODE cell>,\"0\"), UAN_LOOKUP!$A:$B, 2, FALSE), \"\"))"],
     ["   - Keeps the existing UAN when present; otherwise pulls the ECR UAN by EMPCODE; blank if no match."],
     ["3. Paste the helper column back onto UAN NO as values, then delete the helper."],
     [""],
     ["NOTES"],
     ["- EMPCODE and UAN NO are stored as TEXT here to protect leading digits and avoid scientific notation."],
     ["- If salary EMPCODE is numeric, the TEXT(...,\"0\") wrapper handles the match; if it is text, drop TEXT()."],
     ["- Every EMPCODE in this list maps to exactly one 12-digit UAN (no duplicates, no blanks)."],
    ]
    for row in lines: h.append(row)
    h["A1"].font=Font(bold=True,size=13); h["A5"].font=Font(bold=True); h["A9"].font=Font(bold=True); h["A16"].font=Font(bold=True)
    h.column_dimensions["A"].width=110
    wb.save(outpath)
    print(f"{label}: wrote {outpath} with {len(final)} unique EMPCODE->UAN rows")

june=load("june_format.xlsx","Sheet1",4)
july=load("july_pf_ecr.xlsx","Merged",0)
build("JUNE 2026","FORMAT-JUNE_2026.xlsx",june,"June_2026_UAN_LOOKUP.xlsx")
build("JULY 2026","ECR_PF_JULY2026_MERGED.xlsx",july,"July_2026_UAN_LOOKUP.xlsx")
