#!/usr/bin/env python3
"""
Bright Autocomp Private Limited — Liquidation tax model builder.

Reproducibly generates an editable Excel workbook (live formulas) and a Word
summary that work out the tax on liquidating the company, at BOTH levels:
  - Company level: capital gains on realising assets (mainly the Manesar land)
  - Shareholder level: deemed dividend u/s 2(22)(c) + capital gains u/s 46(2)

Source: audited financials for FY2024-25 (figures in the PDF are in Rs. '00;
here they are converted to actual Rupees). NOT tax advice — a planning model.
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ figures
# All converted from "Rs. '00" in the financials to actual Rupees (x100).
PAID_UP_CAPITAL   = 1000.00    * 100     # 10,000 shares x Rs.10
RESERVES          = 51896.68   * 100     # Reserve & Surplus (accumulated profits)
LAND_BUILDING     = 145748.47  * 100     # PPE - Land & Building (WDV = cost, 0% dep)
FD_INVESTMENT     = 244.30     * 100
TRADE_RECV        = 2774.60    * 100
CASH              = 61761.95   * 100
LT_BORROWINGS     = 1820.00    * 100     # security deposits (rent)
ST_BORROWINGS     = 154250.00  * 100     # loan from related parties
TRADE_PAYABLES    = 126.57     * 100
OTHER_CL          = 275.24     * 100
ST_PROVISIONS     = 1160.83    * 100

OTHER_ASSETS      = FD_INVESTMENT + TRADE_RECV + CASH
EXT_LIABILITIES   = (LT_BORROWINGS + ST_BORROWINGS + TRADE_PAYABLES +
                     OTHER_CL + ST_PROVISIONS)
NET_ASSETS_BOOK   = PAID_UP_CAPITAL + RESERVES

# ------------------------------------------------------------------ styles
TITLE  = Font(name="Calibri", size=15, bold=True, color="1F3864")
H2     = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
BOLD   = Font(name="Calibri", size=11, bold=True)
NORM   = Font(name="Calibri", size=11)
MUT    = Font(name="Calibri", size=9, italic=True, color="808080")
HEADFILL = PatternFill("solid", fgColor="1F3864")
INPUTFILL= PatternFill("solid", fgColor="FFF2CC")   # yellow = editable
TOTFILL  = PatternFill("solid", fgColor="D9E1F2")
WARNFILL = PatternFill("solid", fgColor="FCE4D6")
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
RUP = u'₹ #,##0'

wb = Workbook()
ws = wb.active
ws.title = "Liquidation Tax Model"
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 3
ws.column_dimensions["B"].width = 52
ws.column_dimensions["C"].width = 20
ws.column_dimensions["D"].width = 20
ws.column_dimensions["E"].width = 20
ws.column_dimensions["F"].width = 42

r = 1
def row_h(txt, span=("B","F")):
    global r
    ws[f"B{r}"] = txt
    for col in ["B","C","D","E","F"]:
        ws[f"{col}{r}"].fill = HEADFILL
        ws[f"{col}{r}"].font = H2
    r += 1

def line(label, ref_or_val, fmt=RUP, note="", bold=False, fill=None, inp=False):
    global r
    ws[f"B{r}"] = label
    ws[f"B{r}"].font = BOLD if bold else NORM
    c = ws[f"C{r}"]
    c.value = ref_or_val
    c.number_format = fmt
    c.font = BOLD if bold else NORM
    c.alignment = Alignment(horizontal="right")
    if inp:
        c.fill = INPUTFILL
        c.border = BORDER
    if fill:
        for col in ["B","C"]:
            ws[f"{col}{r}"].fill = fill
    if note:
        ws[f"F{r}"] = note
        ws[f"F{r}"].font = MUT
    rr = r
    r += 1
    return f"C{rr}"

def blank():
    global r
    r += 1

# ---------------------------------------------------------------- title
ws[f"B{r}"] = "BRIGHT AUTOCOMP PRIVATE LIMITED — Liquidation Tax Model"
ws[f"B{r}"].font = TITLE
r += 1
ws[f"B{r}"] = ("CIN U35122HR2007PTC037071 · based on audited financials FY2024-25 · "
               "all amounts in actual Rupees (financials were in Rs.'00). Planning model, not tax advice.")
ws[f"B{r}"].font = MUT
r += 2

# ---------------------------------------------------------------- extracted
row_h("A.  EXTRACTED FROM FINANCIALS (31 March 2025)")
cap  = line("Paid-up equity share capital (10,000 x Rs.10)", PAID_UP_CAPITAL)
res  = line("Reserve & Surplus  = accumulated profits", RESERVES,
            note="Deemed-dividend base u/s 2(22)(c)")
land = line("Land & Building — book value / WDV", LAND_BUILDING,
            note="IMT Manesar plot · 0% depreciation · likely worth MUCH more at market")
oth  = line("Other assets (FD + receivables + cash)", OTHER_ASSETS)
liab = line("Total external liabilities (incl. Rs.1.54 cr related-party loan)", EXT_LIABILITIES,
            note="Must be repaid before any distribution to shareholders")
na   = line("Net assets at book (= shareholders' funds)", f"={cap}+{res}", bold=True, fill=TOTFILL,
            note="Book value distributable if assets fetch only book value")
blank()

# ---------------------------------------------------------------- assumptions
row_h("B.  ASSUMPTIONS  — edit the yellow cells")
fmv   = line("Land & Building — MARKET VALUE (FMV) on sale", LAND_BUILDING, inp=True,
             note="** KEY INPUT ** default = book. Enter the real Manesar market value.")
lcost = line("Cost of Land for capital-gains (indexed cost if opting)", LAND_BUILDING, inp=True,
             note="Original cost; no indexation under the 12.5% regime")
lrate = line("Company LTCG rate %  (post 23-Jul-2024 = 12.5)", 12.5, fmt='0.0', inp=True)
csur  = line("Company surcharge %  (7 if income <=10cr, else 12)", 12.0, fmt='0.0', inp=True)
cess  = line("Health & education cess %", 4.0, fmt='0.0', inp=True)
shr   = line("Shareholders' marginal tax rate % (incl. cess)", 31.2, fmt='0.0', inp=True,
             note="Deemed dividend taxed at slab; 31.2 = 30%+cess. Use 35.88/39 if surcharge applies")
scost = line("Cost of acquisition of shares (both shareholders)", PAID_UP_CAPITAL, inp=True,
             note="Subscribed at par, no bonus (Note 3.4)")
blank()

# ---------------------------------------------------------------- company level
row_h("C.  COMPANY-LEVEL TAX  (on realising assets to raise cash)")
cgain = line("Capital gain on Land & Building  = FMV - cost", f"=MAX(0,{fmv}-{lcost})",
             note="Sec 45; nil if land sold only at book value")
ctax  = line("Company LTCG tax  = gain x rate x (1+surcharge) x (1+cess)",
             f"=ROUND({cgain}*{lrate}/100*(1+{csur}/100)*(1+{cess}/100),0)", bold=True, fill=TOTFILL,
             note="Payable by the company before distributing")
blank()

# ---------------------------------------------------------------- distributable
row_h("D.  AMOUNT DISTRIBUTABLE TO SHAREHOLDERS")
bprofit = line("Book profit on land sale (FMV - book)", f"=MAX(0,{fmv}-{land})")
resaft  = line("Accumulated profits after sale (net of company tax)",
               f"={res}+{bprofit}-{ctax}", note="Reserves + realised gain - company tax")
dist    = line("Total distribution to shareholders", f"={cap}+{resaft}", bold=True, fill=TOTFILL,
               note="Return of capital + post-tax reserves")
blank()

# ---------------------------------------------------------------- shareholder level
row_h("E.  SHAREHOLDER-LEVEL TAX")
ddiv  = line("Deemed dividend u/s 2(22)(c)  = accumulated profits", f"={resaft}",
             note="Taxed as dividend at slab in shareholders' hands")
cg46  = line("Capital gains u/s 46(2)  = distribution - dividend - cost", f"=MAX(0,{dist}-{ddiv}-{scost})",
             note="Usually 0 — the gain flows through reserves as dividend")
rcap  = line("Return of capital (tax-free)  = min(cost, distribution-dividend)",
             f"=MIN({scost},{dist}-{ddiv})", note="Your own money back — not taxed")
dtax  = line("Tax on deemed dividend  = dividend x marginal rate", f"=ROUND({ddiv}*{shr}/100,0)", bold=True)
cg46t = line("Tax on 46(2) capital gains @ 12.5%+cess", f"=ROUND({cg46}*12.5/100*(1+{cess}/100),0)")
shtax = line("TOTAL shareholder tax (both shareholders)", f"={dtax}+{cg46t}", bold=True, fill=TOTFILL)
blank()

# ---------------------------------------------------------------- per shareholder
row_h("F.  PER SHAREHOLDER  (Bikram Singh Chadha 50% · Sonu Chadha 50%)")
ws[f"C{r-0}"]  # noop
ws[f"C{r}"] = "Each (50%)"; ws[f"C{r}"].font = BOLD; ws[f"C{r}"].alignment = Alignment(horizontal="right")
r += 1
pdist = line("Distribution received", f"={dist}/2")
pddiv = line("  of which deemed dividend", f"={ddiv}/2")
prcap = line("  of which tax-free return of capital", f"={rcap}/2")
ptax  = line("Personal tax payable", f"=({dtax}+{cg46t})/2", bold=True)
pnet  = line("Net in hand after personal tax", f"={pdist}-{ptax}", bold=True, fill=TOTFILL)
blank()

# ---------------------------------------------------------------- summary
row_h("G.  SUMMARY — total tax cost of liquidation")
s1 = line("Company-level tax", f"={ctax}")
s2 = line("Shareholder-level tax", f"={shtax}")
tot= line("TOTAL TAX (company + shareholders)", f"={ctax}+{shtax}", bold=True, fill=TOTFILL)
netall = line("Net reaching shareholders after ALL tax", f"={dist}-{shtax}", bold=True)
eff= line("Total tax as % of amount realised", f"=({ctax}+{shtax})/({dist}+{ctax})", fmt='0.0%')
blank()

# notes block
notes = [
 "KEY POINTS",
 "1. At BOOK value (default) the tax is modest: deemed dividend on Rs.51.9L reserves at slab; capital gains nil "
 "(the Rs.1L over reserves = paid-up capital = cost). Company tax nil (land at book).",
 "2. The REAL driver is the Manesar land. Enter its market value in the yellow FMV cell: the gain is taxed at the "
 "company (12.5% LTCG + surcharge + cess), and the post-tax gain swells the reserves, so shareholders pay slab tax "
 "on a much larger deemed dividend. Total tax rises steeply with FMV.",
 "3. Return of the Rs.1,00,000 paid-up capital is NOT taxed (recovered as cost of shares).",
 "4. The Rs.1.54 cr related-party loan and all creditors must be repaid before shareholders receive anything.",
 "5. TDS u/s 194 may apply on the deemed dividend. Shareholder tax shown at a single marginal rate — actual depends "
 "on each shareholder's total income and surcharge; edit the rate cell.",
 "6. Compare with a statutory conversion to LLP (Sec 47(xiiib)) which can avoid ALL of the above — see the "
 "llp-partner-withdrawal-calculator folder.",
 "Not tax advice. Validate with your CA before acting.",
]
for i, n in enumerate(notes):
    ws[f"B{r}"] = n
    ws[f"B{r}"].font = BOLD if i == 0 else MUT
    ws[f"B{r}"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(f"B{r}:F{r}")
    if i > 0:
        ws.row_dimensions[r].height = 30
    r += 1

MSHEET = "'Liquidation Tax Model'"
# capture cross-sheet references to the main sheet's assumption/figure cells
REF = dict(land=f"{MSHEET}!{land}", res=f"{MSHEET}!{res}", cap=f"{MSHEET}!{cap}",
           lcost=f"{MSHEET}!{lcost}", lrate=f"{MSHEET}!{lrate}", csur=f"{MSHEET}!{csur}",
           cess=f"{MSHEET}!{cess}", shr=f"{MSHEET}!{shr}", scost=f"{MSHEET}!{scost}")

# ================================================================= SCENARIO SHEET
sc = wb.create_sheet("Land FMV Scenarios")
sc.sheet_view.showGridLines = False
sc.column_dimensions["A"].width = 3
sc.column_dimensions["B"].width = 46
for ci in range(3, 9):
    sc.column_dimensions[get_column_letter(ci)].width = 18

sc["B1"] = "Land & Building — Market-Value Sensitivity  (capital-gains tax at each FMV)"
sc["B1"].font = TITLE
sc["B2"] = ("Edit the yellow market-value row — every column recalculates. Rates pull from the "
            "'Liquidation Tax Model' sheet (assumptions section).")
sc["B2"].font = MUT

# scenario FMV values (editable) — book value, then a spread for a Manesar plot
scen_vals = [f"={REF['land']}", 25000000, 50000000, 75000000, 100000000, 150000000]

hdr = 4
sc[f"B{hdr}"] = "Land & Building MARKET VALUE (FMV)  — EDIT ►"
sc[f"B{hdr}"].font = BOLD
for i, v in enumerate(scen_vals):
    col = get_column_letter(3 + i)
    cell = sc[f"{col}{hdr}"]
    cell.value = v
    cell.number_format = RUP
    cell.font = BOLD
    cell.fill = INPUTFILL
    cell.border = BORDER
    cell.alignment = Alignment(horizontal="right")

# metric rows: (label, formula-template using {c}=this column letter and {h}=header row and row refs)
rows_def = [
    ("Company capital gain on land  (FMV − cost)",
     "=MAX(0,{c}{H}-{lcost})", RUP, False),
    ("Company LTCG tax  (rate + surcharge + cess)",
     "=ROUND(R_GAIN*{lrate}/100*(1+{csur}/100)*(1+{cess}/100),0)", RUP, True),
    ("Book profit added to reserves  (FMV − book)",
     "=MAX(0,{c}{H}-{land})", RUP, False),
    ("Accumulated profits after sale  (= deemed dividend)",
     "={res}+R_BPROFIT-R_CTAX", RUP, False),
    ("Total distribution to shareholders",
     "={cap}+R_RESAFT", RUP, False),
    ("Shareholder tax on deemed dividend  (slab)",
     "=ROUND(R_RESAFT*{shr}/100,0)", RUP, True),
    ("Capital gains u/s 46(2)",
     "=MAX(0,R_DIST-R_RESAFT-{scost})", RUP, False),
    ("TOTAL TAX  (company + shareholders)",
     "=R_CTAX+R_SHTAX", RUP, True),
    ("Net reaching shareholders after ALL tax",
     "=R_DIST-R_SHTAX", RUP, True),
    ("Total tax as % of amount realised",
     "=(R_CTAX+R_SHTAX)/(R_DIST+R_CTAX)", '0.0%', True),
]
# assign row numbers
base = hdr + 1
rownum = {name: base + i for i, name in enumerate(
    ["GAIN","CTAX","BPROFIT","RESAFT","DIST","SHTAX","CG46","TOTAL","NET","EFF"])}

for i, (label, tmpl, fmt, strong) in enumerate(rows_def):
    rr = base + i
    sc[f"B{rr}"] = label
    sc[f"B{rr}"].font = BOLD if strong else NORM
    for j in range(6):
        col = get_column_letter(3 + j)
        f = (tmpl
             .replace("{c}", col).replace("{H}", str(hdr))
             .replace("R_GAIN", f"{col}{rownum['GAIN']}")
             .replace("R_CTAX", f"{col}{rownum['CTAX']}")
             .replace("R_BPROFIT", f"{col}{rownum['BPROFIT']}")
             .replace("R_RESAFT", f"{col}{rownum['RESAFT']}")
             .replace("R_DIST", f"{col}{rownum['DIST']}")
             .replace("R_SHTAX", f"{col}{rownum['SHTAX']}")
             .replace("{lcost}", REF['lcost']).replace("{lrate}", REF['lrate'])
             .replace("{csur}", REF['csur']).replace("{cess}", REF['cess'])
             .replace("{land}", REF['land']).replace("{res}", REF['res'])
             .replace("{cap}", REF['cap']).replace("{shr}", REF['shr'])
             .replace("{scost}", REF['scost']))
        cell = sc[f"{col}{rr}"]
        cell.value = f
        cell.number_format = fmt
        cell.font = BOLD if strong else NORM
        cell.alignment = Alignment(horizontal="right")
        if strong:
            cell.fill = TOTFILL
    if strong:
        sc[f"B{rr}"].fill = TOTFILL

note_r = base + len(rows_def) + 1
for i, n in enumerate([
    "How to use: type any market value into the yellow row and read the TOTAL TAX and NET columns.",
    "The company pays 12.5% LTCG (+surcharge +cess) on the land gain; the post-tax gain enlarges the "
    "reserves, so shareholders then pay slab tax on a bigger deemed dividend. That is why total tax climbs "
    "fast with the land value.",
    "Sec 46(2) capital gain stays ~nil because the only sum above reserves is the paid-up capital, which "
    "equals its cost. Return of that capital is tax-free.",
    "Change the rates (LTCG %, surcharge %, shareholder slab %) on the 'Liquidation Tax Model' sheet — every "
    "scenario updates.",
]):
    sc[f"B{note_r+i}"] = n
    sc[f"B{note_r+i}"].font = MUT
    sc[f"B{note_r+i}"].alignment = Alignment(wrap_text=True, vertical="top")
    sc.merge_cells(f"B{note_r+i}:H{note_r+i}")
    sc.row_dimensions[note_r+i].height = 28

# ================================================================= SHAREHOLDER TAX SHEET
sh = wb.create_sheet("Shareholder Tax")
sh.sheet_view.showGridLines = False
sh.column_dimensions["A"].width = 3
sh.column_dimensions["B"].width = 50
sh.column_dimensions["C"].width = 20
sh.column_dimensions["D"].width = 20
sh.column_dimensions["E"].width = 40

sh["B1"] = "Tax in the hands of SHAREHOLDERS on the amount they receive"
sh["B1"].font = TITLE
sh["B2"] = ("Everything a shareholder receives on liquidation falls into three buckets, each taxed "
            "differently. Driven by the FMV on the 'Liquidation Tax Model' sheet.")
sh["B2"].font = MUT

def M(addr):  # main-sheet reference
    return f"{MSHEET}!{addr}"

rr = 4
sh[f"C{rr}"] = "Both (100%)"; sh[f"D{rr}"] = "Each partner (50%)"
for col in ("C", "D"):
    sh[f"{col}{rr}"].font = BOLD; sh[f"{col}{rr}"].alignment = Alignment(horizontal="right")
rr += 1

def srow(label, both_formula, fmt=RUP, bold=False, fill=None, note=""):
    global rr
    sh[f"B{rr}"] = label
    sh[f"B{rr}"].font = BOLD if bold else NORM
    cb = sh[f"C{rr}"]; cb.value = both_formula; cb.number_format = fmt
    cb.font = BOLD if bold else NORM; cb.alignment = Alignment(horizontal="right")
    cd = sh[f"D{rr}"]; cd.value = f"=C{rr}/2" if fmt == RUP else f"=C{rr}"
    cd.number_format = fmt; cd.font = BOLD if bold else NORM
    cd.alignment = Alignment(horizontal="right")
    if fill:
        for col in ("B", "C", "D"):
            sh[f"{col}{rr}"].fill = fill
    if note:
        sh[f"E{rr}"] = note; sh[f"E{rr}"].font = MUT
    rr += 1

srow("TOTAL AMOUNT RECEIVED by shareholders", f"={M(dist)}", bold=True, fill=TOTFILL)
rr += 1
sh[f"B{rr}"] = "Split into three tax buckets:"; sh[f"B{rr}"].font = BOLD; rr += 1
srow("① Return of paid-up capital", f"={M(rcap)}",
     note="TAX-FREE — your own money, recovered as cost of shares u/s 46(2)")
srow("② Deemed dividend u/s 2(22)(c)", f"={M(ddiv)}",
     note="Reserves / accumulated profits — TAXABLE at slab")
srow("③ Capital gains u/s 46(2)", f"={M(cg46)}",
     note="Amount above (dividend + cost) — TAXABLE as LTCG 12.5%")
srow("   Check: buckets ①+②+③ = total received", f"={M(rcap)}+{M(ddiv)}+{M(cg46)}",
     note="Must equal the total amount received above")
rr += 1
sh[f"B{rr}"] = "Tax on each bucket:"; sh[f"B{rr}"].font = BOLD; rr += 1
srow("Tax on ① return of capital", "=0", note="Nil — not income")
srow("Tax on ② deemed dividend  (at marginal slab)", f"={M(dtax)}",
     note=f"= dividend x shareholders' rate cell")
srow("Tax on ③ capital gains 46(2) @ 12.5% + cess", f"={M(cg46t)}")
srow("TOTAL TAX in shareholders' hands", f"={M(dtax)}+{M(cg46t)}", bold=True, fill=TOTFILL)
srow("NET RETAINED after tax", f"={M(dist)}-{M(dtax)}-{M(cg46t)}", bold=True)
srow("Effective tax rate on amount received", f"=({M(dtax)}+{M(cg46t)})/{M(dist)}",
     fmt='0.0%', bold=True)

rr += 1
for n in [
    "Bottom line on the CAPITAL a shareholder receives: the return of the Rs.1,00,000 paid-up capital "
    "(Rs.50,000 each) is TAX-FREE. What is taxed is the reserves (as deemed dividend at slab) and any "
    "surplus over cost (as capital gains). At book value there is no capital gain, so only the reserves "
    "are taxed.",
    "Raise the land FMV on the model sheet and bucket ② (deemed dividend) grows — that is where the tax is.",
    "TDS u/s 194 may be deducted by the company on the deemed dividend. Not tax advice.",
]:
    sh[f"B{rr}"] = n; sh[f"B{rr}"].font = MUT
    sh[f"B{rr}"].alignment = Alignment(wrap_text=True, vertical="top")
    sh.merge_cells(f"B{rr}:E{rr}"); sh.row_dimensions[rr].height = 30; rr += 1

# order the sheets sensibly
wb.move_sheet("Shareholder Tax", -(len(wb.sheetnames)-2))

xlsx_path = os.path.join(HERE, "Bright_Autocomp_Liquidation_Tax.xlsx")
wb.save(xlsx_path)
print("Wrote", xlsx_path)

# ================================================================= Word doc
def money(x): return u"₹ {:,.0f}".format(round(x))

# recompute default (book value) scenario for the Word narrative
gain = max(0, LAND_BUILDING - LAND_BUILDING)          # 0 at book
ctax_v = round(gain * 0.125 * 1.12 * 1.04)            # 0
bprofit_v = max(0, LAND_BUILDING - LAND_BUILDING)
resaft_v = RESERVES + bprofit_v - ctax_v
dist_v = PAID_UP_CAPITAL + resaft_v
ddiv_v = resaft_v
cg46_v = max(0, dist_v - ddiv_v - PAID_UP_CAPITAL)
dtax_v = round(ddiv_v * 0.312)
shtax_v = dtax_v + round(cg46_v * 0.125 * 1.04)
total_v = ctax_v + shtax_v

doc = Document()
h = doc.add_heading("Bright Autocomp Private Limited — Liquidation Tax Implications", level=0)
p = doc.add_paragraph()
run = p.add_run("Based on audited financials FY2024-25 (CIN U35122HR2007PTC037071). "
                "Figures converted to actual Rupees. This is a planning summary, not tax advice.")
run.italic = True; run.font.size = Pt(9)

doc.add_heading("The two-level tax on liquidation", level=1)
doc.add_paragraph(
    "When the company is wound up and its assets are distributed to the two shareholders "
    "(Bikram Singh Chadha 50% and Sonu Chadha 50%), tax arises at up to three points:")
for t in [
    "Company level — Sec 46(1) + Sec 45: if assets (mainly the IMT Manesar land) are SOLD to raise cash, "
    "the company pays capital-gains tax on the gain over cost before distributing.",
    "Shareholder level — Sec 2(22)(c): the distribution, to the extent of accumulated profits (Reserve & "
    "Surplus), is a DEEMED DIVIDEND taxed at each shareholder's slab rate.",
    "Shareholder level — Sec 46(2): any amount received above (deemed dividend + cost of shares) is CAPITAL "
    "GAINS. The return of paid-up capital itself equals the cost and is therefore NOT taxed.",
]:
    doc.add_paragraph(t, style="List Bullet")

doc.add_heading("Key figures from the financials", level=1)
tbl = doc.add_table(rows=1, cols=2); tbl.style = "Light Grid Accent 1"
tbl.rows[0].cells[0].text = "Item"; tbl.rows[0].cells[1].text = "Amount (Rs.)"
for label, val in [
    ("Paid-up share capital (10,000 x Rs.10)", PAID_UP_CAPITAL),
    ("Reserve & Surplus (accumulated profits)", RESERVES),
    ("Land & Building — book value (Manesar)", LAND_BUILDING),
    ("Other assets (FD + receivables + cash)", OTHER_ASSETS),
    ("Total external liabilities", EXT_LIABILITIES),
    ("Net assets at book (distributable at book)", NET_ASSETS_BOOK),
]:
    c = tbl.add_row().cells; c[0].text = label; c[1].text = money(val)

doc.add_heading("Scenario 1 — assets realise only BOOK value", level=1)
tbl2 = doc.add_table(rows=1, cols=2); tbl2.style = "Light Grid Accent 1"
tbl2.rows[0].cells[0].text = "Head"; tbl2.rows[0].cells[1].text = "Amount (Rs.)"
for label, val in [
    ("Company capital-gains tax (land at book)", ctax_v),
    ("Deemed dividend u/s 2(22)(c)", ddiv_v),
    ("Tax on deemed dividend @ 31.2%", dtax_v),
    ("Capital gains u/s 46(2)", cg46_v),
    ("Return of capital (tax-free)", PAID_UP_CAPITAL),
    ("TOTAL TAX (company + shareholders)", total_v),
    ("Net reaching shareholders after all tax", dist_v - shtax_v),
]:
    c = tbl2.add_row().cells; c[0].text = label; c[1].text = money(val)
doc.add_paragraph(
    "Per shareholder: distribution ~{}, of which tax-free capital {}; personal tax ~{}."
    .format(money(dist_v/2), money(PAID_UP_CAPITAL/2), money(shtax_v/2)))

doc.add_heading("Scenario 2 — the real driver: Manesar land at MARKET value", level=1)
warn = doc.add_paragraph()
wr = warn.add_run(
    "The Land & Building sits at only " + money(LAND_BUILDING) + " (book, 0% depreciation), but an industrial "
    "plot in IMT Manesar Sector-3 is very likely worth several times that. If it is sold at market value: (a) the "
    "company pays 12.5% LTCG + surcharge + cess on the gain, and (b) the post-tax gain swells the reserves, so the "
    "shareholders pay slab tax on a much larger deemed dividend. The total tax can run into crores. The Excel model "
    "lets you enter the actual market value and see the number instantly.")
wr.bold = True
doc.add_paragraph(
    "Because the entire appreciation flows through the P&L into reserves, it is caught as deemed dividend under "
    "2(22)(c); the Sec 46(2) capital gain stays ~nil (the only amount above reserves is the paid-up capital, which "
    "equals cost). So the shareholder-level tax is essentially slab tax on the whole enlarged reserve.")

doc.add_heading("Important caveats", level=1)
for t in [
    "The Rs.1.54 cr related-party loan and all creditors must be repaid before shareholders receive anything.",
    "TDS u/s 194 may apply on the deemed dividend.",
    "Shareholder tax is shown at a single marginal rate (31.2%); the real figure depends on each shareholder's "
    "total income and applicable surcharge.",
    "A statutory conversion to LLP under Sec 47(xiiib) can avoid almost all of this tax — consider it before "
    "liquidating. See the accompanying LLP calculator.",
    "Not tax advice — validate every figure with your CA.",
]:
    doc.add_paragraph(t, style="List Bullet")

docx_path = os.path.join(HERE, "Bright_Autocomp_Liquidation_Tax.docx")
doc.save(docx_path)
print("Wrote", docx_path)

# print verification
print("\n--- BOOK-VALUE SCENARIO (verification) ---")
print("Deemed dividend :", money(ddiv_v))
print("Company tax     :", money(ctax_v))
print("Shareholder tax :", money(shtax_v))
print("TOTAL tax       :", money(total_v))
print("Net to holders  :", money(dist_v - shtax_v))
