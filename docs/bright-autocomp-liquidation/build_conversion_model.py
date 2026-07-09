#!/usr/bin/env python3
"""
Bright Autocomp Private Limited — STATUTORY CONVERSION to LLP model.

Uses the company's ACTUAL audited FY2024-25 figures to show:
  1. Sec 47(xiiib) eligibility (turnover / asset tests)
  2. Route comparison: conversion (tax ~0) vs liquidation (driven by land FMV)
  3. How the two partners draw money from the converted LLP each year
     (interest on capital + Sec 40(b) remuneration + tax-free profit share)

Figures in the financials are in Rs.'00; here converted to actual Rupees.
Planning model, not tax advice.
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from docx import Document
from docx.shared import Pt
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- actual figures (x100 from Rs.'00) ----------------
PAID_UP_CAPITAL = 1000.00   * 100          # 1,00,000
RESERVES        = 51896.68  * 100          # 51,89,668  accumulated profits
LAND_BUILDING   = 145748.47 * 100          # 1,45,74,847 book
TOTAL_ASSETS    = 210529.32 * 100          # 2,10,52,932
NET_WORTH       = PAID_UP_CAPITAL + RESERVES   # 52,89,668  -> becomes LLP capital
PBT_FY25        = 21758.49  * 100          # 21,75,849  profit before tax
REV_FY25        = 22248.83  * 100          # 22,24,883
REV_FY24        = 16185.96  * 100          # 16,18,596

# ---------------- styles ----------------
TITLE = Font(size=15, bold=True, color="1F3864")
H2    = Font(size=11, bold=True, color="FFFFFF")
BOLD  = Font(size=11, bold=True)
NORM  = Font(size=11)
MUT   = Font(size=9, italic=True, color="808080")
OKF   = Font(size=11, bold=True, color="2E7D32")
HEADFILL = PatternFill("solid", fgColor="1F3864")
INPUTFILL= PatternFill("solid", fgColor="FFF2CC")
TOTFILL  = PatternFill("solid", fgColor="D9E1F2")
OKFILL   = PatternFill("solid", fgColor="E2EFDA")
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
RUP = u'₹ #,##0'

wb = Workbook()

# =================================================================== SHEET 1
ws = wb.active
ws.title = "Conversion vs Liquidation"
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 3
ws.column_dimensions["B"].width = 50
ws.column_dimensions["C"].width = 20
ws.column_dimensions["D"].width = 20
ws.column_dimensions["E"].width = 42
r = 1
def H(txt, s=ws):
    global r
    s[f"B{r}"] = txt
    for c in ["B","C","D","E"]:
        s[f"{c}{r}"].fill = HEADFILL; s[f"{c}{r}"].font = H2
    r += 1
def L(label, val, s=ws, fmt=RUP, note="", bold=False, fill=None, inp=False, font=None):
    global r
    s[f"B{r}"] = label; s[f"B{r}"].font = font or (BOLD if bold else NORM)
    c = s[f"C{r}"]; c.value = val; c.number_format = fmt
    c.font = font or (BOLD if bold else NORM); c.alignment = Alignment(horizontal="right")
    if inp: c.fill = INPUTFILL; c.border = BORDER
    if fill:
        for cc in ["B","C"]: s[f"{cc}{r}"].fill = fill
    if note: s[f"E{r}"] = note; s[f"E{r}"].font = MUT
    r += 1
    return f"C{r-1}"
def BL():
    global r; r += 1

ws[f"B{r}"] = "BRIGHT AUTOCOMP PRIVATE LIMITED — Conversion to LLP vs Liquidation"; ws[f"B{r}"].font = TITLE; r+=1
ws[f"B{r}"] = ("Actual audited FY2024-25 figures (converted from Rs.'00). Two partners 50:50 — "
              "Bikram Singh Chadha & Sonu Chadha. Planning model, not tax advice."); ws[f"B{r}"].font = MUT; r+=2

H("A.  SEC 47(xiiib) ELIGIBILITY — can the company convert tax-free?")
tv = L("Turnover FY2024-25", REV_FY25, note="Sale of goods & services (Note 17)")
tv2 = L("Turnover FY2023-24", REV_FY24, note="Prior year (Note 17)")
lim = L("Limit — turnover must be <= Rs.60,00,000 in each of 3 prior years", 6000000, inp=True)
L("  → Turnover test", f'=IF(AND({tv}<={lim},{tv2}<={lim}),"PASS — eligible","CHECK")', fmt="General",
  bold=True, font=OKF, note="Confirm FY2022-23 turnover with CA")
ta = L("Total assets (book)", TOTAL_ASSETS, note="Balance sheet total")
alim = L("Limit — total assets must be <= Rs.5,00,00,000", 50000000, inp=True)
L("  → Asset test", f'=IF({ta}<={alim},"PASS — eligible","CHECK")', fmt="General", bold=True, font=OKF)
ws[f"B{r}"]=("Other conditions (must all hold): all shareholders become partners in same proportion; "
             "they keep >=50% profit share for 5 years; NO payout from accumulated profits for 3 years; "
             "no consideration other than LLP profit/capital share.")
ws[f"B{r}"].font=MUT; ws[f"B{r}"].alignment=Alignment(wrap_text=True, vertical="top")
ws.merge_cells(f"B{r}:E{r}"); ws.row_dimensions[r].height=42; r+=1
BL()

H("B.  ROUTE COMPARISON  (edit the yellow land market value)")
fmv  = L("Land & Building — MARKET VALUE (FMV)", LAND_BUILDING, inp=True,
         note="** KEY ** default = book. Enter real Manesar market value.")
lrate= L("Company LTCG rate % (liquidation only)", 12.5, fmt='0.0', inp=True)
csur = L("Company surcharge %", 12.0, fmt='0.0', inp=True)
cess = L("Cess %", 4.0, fmt='0.0', inp=True)
shr  = L("Shareholder / partner marginal rate %", 31.2, fmt='0.0', inp=True)
BL()
ws[f"B{r}"]="ROUTE 1 — STATUTORY CONVERSION (Sec 47(xiiib))"; ws[f"B{r}"].font=BOLD; r+=1
c_cg = L("Capital gains tax on transfer of assets", 0, fill=OKFILL, note="EXEMPT u/s 47(xiiib)")
c_dd = L("Deemed dividend / distribution tax", 0, fill=OKFILL, note="None — no distribution")
c_sd = L("Stamp duty on assets", 0, fill=OKFILL, note="Usually exempt/concessional on conversion")
conv_tot = L("TOTAL one-time tax — CONVERSION", "=C%d+C%d+C%d" % (
    int(c_cg[1:]), int(c_dd[1:]), int(c_sd[1:])), bold=True, fill=OKFILL, font=OKF)
BL()
ws[f"B{r}"]="ROUTE 2 — LIQUIDATE THE COMPANY"; ws[f"B{r}"].font=BOLD; r+=1
gain = L("Company capital gain on land (FMV − cost)", f"=MAX(0,{fmv}-{LAND_BUILDING})")
ctax = L("Company LTCG tax", f"=ROUND({gain}*{lrate}/100*(1+{csur}/100)*(1+{cess}/100),0)")
resaft = L("Accumulated profits after sale (= deemed dividend)", f"={RESERVES}+MAX(0,{fmv}-{LAND_BUILDING})-{ctax}")
ddtax = L("Shareholder tax on deemed dividend (slab)", f"=ROUND({resaft}*{shr}/100,0)")
liq_tot = L("TOTAL one-time tax — LIQUIDATION", f"={ctax}+{ddtax}", bold=True, fill=TOTFILL)
BL()
saved = L("TAX SAVED BY CONVERTING (instead of liquidating)", f"={liq_tot}-{conv_tot}",
          bold=True, fill=OKFILL, font=OKF, note="Conversion avoids the entire liquidation tax")
BL()

# =================================================================== SHEET 2
w2 = wb.create_sheet("LLP Annual Withdrawals")
w2.sheet_view.showGridLines = False
for col,wd in [("A",3),("B",50),("C",20),("D",20),("E",20),("F",40)]:
    w2.column_dimensions[col].width = wd
r = 1
def H2s(t): H(t, s=w2)
def L2(label,val,fmt=RUP,note="",bold=False,fill=None,inp=False,font=None):
    global r
    w2[f"B{r}"]=label; w2[f"B{r}"].font=font or (BOLD if bold else NORM)
    c=w2[f"C{r}"]; c.value=val; c.number_format=fmt; c.font=font or (BOLD if bold else NORM)
    c.alignment=Alignment(horizontal="right")
    if inp: c.fill=INPUTFILL; c.border=BORDER
    if fill:
        for cc in ["B","C"]: w2[f"{cc}{r}"].fill=fill
    if note: w2[f"F{r}"]=note; w2[f"F{r}"].font=MUT
    r+=1; return f"C{r-1}"

w2[f"B{r}"]="How the two partners draw money from the converted LLP (per year)"; w2[f"B{r}"].font=TITLE; r+=1
w2[f"B{r}"]="Based on the company's actual annual profit. Edit the yellow cells."; w2[f"B{r}"].font=MUT; r+=2

H2s("A.  INPUTS  (yellow = editable)")
prof = L2("Annual book profit before partner rem & interest", PBT_FY25, inp=True,
          note="= company PBT FY25; edit for future years")
cap  = L2("LLP capital (carried from company net worth)", NET_WORTH, inp=True,
          note="Capital 1,00,000 + reserves 51,89,668")
irate= L2("Interest on capital rate % (max 12 deductible)", 12.0, fmt='0.0', inp=True)
pr   = L2("Partners' marginal tax rate % (incl cess)", 31.2, fmt='0.0', inp=True)
BL2 = lambda: None
r += 1

H2s("B.  THE THREE WITHDRAWAL ROUTES")
intcap = L2("① Interest on capital = capital × rate", f"=ROUND({cap}*{irate}/100,0)",
            note="Deductible for LLP; taxable to partners at slab")
bookaft= L2("Book profit after interest (for Sec 40(b))", f"={prof}-{intcap}")
# 40(b): first 6L -> max(3L, 90%); balance 60%
cap40b = L2("② Remuneration — Sec 40(b) deductible cap",
            f"=MAX(300000,MIN({bookaft},600000)*0.9)+MAX(0,{bookaft}-600000)*0.6",
            note="Working-partner remuneration, split 50:50; taxable at slab")
llptax = L2("LLP taxable income = book profit − interest − remuneration", f"={bookaft}-{cap40b}")
tllp   = L2("LLP tax @ 30% + 4% cess", f"=ROUND(IF({llptax}>0,{llptax}*0.30*1.04,0),0)", bold=True)
psh    = L2("③ Profit share pool (tax-free, 50:50)", f"={prof}-{intcap}-{cap40b}-{tllp}",
            bold=True, fill=OKFILL, note="Exempt u/s 10(2A)")
BL2()
r += 1

H2s("C.  TOTAL DRAWN & TAX")
totdraw= L2("Total drawn by partners (interest + remuneration + profit share)",
            f"={intcap}+{cap40b}+{psh}", bold=True, fill=TOTFILL)
taxable= L2("Taxable portion (interest + remuneration)", f"={intcap}+{cap40b}")
ptax   = L2("Partner tax on that (at marginal rate)", f"=ROUND(({intcap}+{cap40b})*{pr}/100,0)")
alltax = L2("TOTAL TAX (LLP + partners)", f"={tllp}+{ptax}", bold=True, fill=TOTFILL)
nethand= L2("Net in partners' hands after all tax", f"={totdraw}-{ptax}", bold=True, fill=OKFILL, font=OKF)
BL2(); r+=1
L2("Per partner — total drawn (50%)", f"={totdraw}/2")
L2("Per partner — net in hand (50%)", f"={nethand}/2", bold=True)
BL2(); r+=1

for n in [
 "PLUS: interest on capital of "
 "~Rs.6.3L/yr is a clean recurring, deductible withdrawal on the Rs.52.9L capital.",
 "The Rs.52.9L capital itself (ex-reserves) is LOCKED for 3 years under Sec 47(xiiib) — do not return it "
 "as capital before then, or the conversion becomes taxable. Interest/remuneration/profit share are fine.",
 "After 3 years, capital can be withdrawn tax-free (return of capital) subject to the LLP agreement, "
 "solvency, and CA sign-off.",
 "Not tax advice — validate with your CA.",
]:
    w2[f"B{r}"]=n; w2[f"B{r}"].font=MUT
    w2[f"B{r}"].alignment=Alignment(wrap_text=True, vertical="top")
    w2.merge_cells(f"B{r}:F{r}"); w2.row_dimensions[r].height=30; r+=1

xlsx = os.path.join(HERE, "Bright_Autocomp_Conversion_to_LLP.xlsx")
wb.save(xlsx); print("Wrote", xlsx)

# =================================================================== WORD
def money(x): return u"₹ {:,.0f}".format(round(x))
# compute annual withdrawal (default) for narrative
intcap_v = round(NET_WORTH*0.12)
bookaft_v = PBT_FY25 - intcap_v
cap40b_v = max(300000, min(bookaft_v,600000)*0.9) + max(0,bookaft_v-600000)*0.6
llptax_v = bookaft_v - cap40b_v
tllp_v = round(llptax_v*0.30*1.04) if llptax_v>0 else 0
psh_v = PBT_FY25 - intcap_v - cap40b_v - tllp_v
totdraw_v = intcap_v + cap40b_v + psh_v
ptax_v = round((intcap_v+cap40b_v)*0.312)
alltax_v = tllp_v + ptax_v
nethand_v = totdraw_v - ptax_v

doc = Document()
doc.add_heading("Bright Autocomp Private Limited — Conversion to LLP", 0)
p=doc.add_paragraph(); rr=p.add_run("Actual audited FY2024-25 figures. Two partners 50:50. Planning summary, not tax advice."); rr.italic=True; rr.font.size=Pt(9)

doc.add_heading("1. The company is eligible for a TAX-NEUTRAL conversion", 1)
doc.add_paragraph(
    "Under Sec 47(xiiib), a Pvt Ltd can convert to an LLP with NO capital-gains tax if turnover is "
    "under Rs.60 lakh in each of the 3 preceding years and book assets are under Rs.5 crore. Bright "
    "Autocomp: turnover Rs.{:,.0f} (FY25) and Rs.{:,.0f} (FY24) — well under Rs.60 lakh; book assets "
    "Rs.{:,.0f} — under Rs.5 crore. So it QUALIFIES (confirm FY23 turnover and the continuity conditions "
    "with your CA).".format(REV_FY25, REV_FY24, TOTAL_ASSETS))

doc.add_heading("2. Conversion vs liquidation — the tax saved", 1)
doc.add_paragraph(
    "Conversion transfers all assets (including the Manesar land) to the LLP with NO capital-gains tax, "
    "NO deemed dividend and NO stamp duty. Liquidation instead triggers company capital-gains tax on the "
    "land plus deemed-dividend tax on the reserves — from ~Rs.16 lakh at book value up to several crore "
    "at market value. Conversion avoids all of it.")

doc.add_heading("3. How partners draw money from the converted LLP (per year)", 1)
t=doc.add_table(rows=1, cols=2); t.style="Light Grid Accent 1"
t.rows[0].cells[0].text="Route"; t.rows[0].cells[1].text="Amount (Rs.)"
for lab,val in [
    ("① Interest on capital @12% on Rs.52.9L", intcap_v),
    ("② Remuneration (Sec 40(b) cap)", cap40b_v),
    ("③ Profit share (tax-free, 10(2A))", psh_v),
    ("Total drawn by partners", totdraw_v),
    ("LLP tax", tllp_v),
    ("Partner tax (on interest + remuneration)", ptax_v),
    ("Net in partners' hands after all tax", nethand_v),
]:
    c=t.add_row().cells; c[0].text=lab; c[1].text=money(val)
doc.add_paragraph(
    "So on the current ~Rs.21.8L annual profit the partners can pull out ~{} between them, with only ~{} "
    "of total tax. The Rs.52.9L capital (ex-reserves) stays locked for 3 years under Sec 47(xiiib); "
    "interest, remuneration and profit share are unaffected.".format(money(totdraw_v), money(alltax_v)))

doc.add_heading("Caveats", 1)
for tx in [
    "Sec 47(xiiib) conditions must ALL hold — same partners/proportions, >=50% profit share for 5 years, "
    "no payout from accumulated profits (the Rs.52.9L) for 3 years.",
    "Interest on capital deductible only up to 12% and if authorised in the LLP agreement.",
    "Confirm FY2022-23 turnover and current-year rates/limits with your CA.",
    "Not tax advice.",
]:
    doc.add_paragraph(tx, style="List Bullet")

docx = os.path.join(HERE, "Bright_Autocomp_Conversion_to_LLP.docx")
doc.save(docx); print("Wrote", docx)

print("\n--- ANNUAL LLP WITHDRAWAL (verification) ---")
print("Interest on capital:", money(intcap_v))
print("Remuneration 40(b) :", money(cap40b_v))
print("Profit share (free):", money(psh_v))
print("Total drawn        :", money(totdraw_v))
print("LLP tax            :", money(tllp_v))
print("Partner tax        :", money(ptax_v))
print("Net in hand        :", money(nethand_v))
