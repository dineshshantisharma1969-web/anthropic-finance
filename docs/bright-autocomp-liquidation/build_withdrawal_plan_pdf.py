#!/usr/bin/env python3
"""Bright Autocomp — Maximum Withdrawal Plan as a PDF (opens on any device).
Mirrors the Word doc; uses 'Rs.' (core PDF fonts are latin-1)."""
from fpdf import FPDF
import os
HERE = os.path.dirname(os.path.abspath(__file__))

# figures (x100 from Rs.'00)
CAPITAL=100000; RESERVES=5189668; LOAN=15425000
CASH=6176195; RECV=277460; FD=24430; LAND=14574847
LIQUID=CASH+RECV+FD; GAP=LOAN-LIQUID
def rs(x): return "Rs. {:,.0f}".format(round(x))

NAVY=(31,56,100); GREEN=(46,125,50); GREY=(120,120,120); LT=(217,225,242); LG=(226,239,218)

class PDF(FPDF):
    def header(self):
        if self.page_no()==1: return
        self.set_font("Helvetica","I",8); self.set_text_color(*GREY)
        self.cell(0,6,"Bright Autocomp Pvt Ltd - Maximum Withdrawal Plan",0,1,"R")
    def footer(self):
        self.set_y(-12); self.set_font("Helvetica","I",7); self.set_text_color(*GREY)
        self.cell(0,6,"Planning note, not tax advice - validate with your CA.   Page %d"%self.page_no(),0,0,"C")

def h1(pdf,t):
    pdf.ln(2); pdf.set_x(pdf.l_margin); pdf.set_font("Helvetica","B",12); pdf.set_text_color(*NAVY)
    pdf.multi_cell(0,7,t); pdf.set_text_color(0,0,0); pdf.ln(1)
def body(pdf,t,bold=False):
    pdf.set_x(pdf.l_margin); pdf.set_font("Helvetica","B" if bold else "",10.5); pdf.set_text_color(0,0,0)
    pdf.multi_cell(0,5.5,t); pdf.ln(1)
def bullet(pdf,t):
    pdf.set_x(pdf.l_margin); pdf.set_font("Helvetica","",10.5); pdf.set_text_color(0,0,0)
    pdf.cell(5,5.5,chr(149)); pdf.set_x(pdf.l_margin+5)
    pdf.multi_cell(0,5.5,t); pdf.ln(0.5)

def table(pdf, rows, widths, header_fill=NAVY, total_idx=None, green_rows=()):
    pdf.set_font("Helvetica","B",9.5)
    pdf.set_fill_color(*header_fill); pdf.set_text_color(255,255,255)
    for i,c in enumerate(rows[0]):
        pdf.cell(widths[i],7,c,1,0,"L" if i==0 else "R",True)
    pdf.ln()
    pdf.set_text_color(0,0,0)
    for ri,row in enumerate(rows[1:]):
        tot = (total_idx is not None and ri==total_idx)
        grn = ri in green_rows
        pdf.set_font("Helvetica","B" if (tot or grn) else "",9.5)
        if tot: pdf.set_fill_color(*LT); fill=True
        elif grn: pdf.set_fill_color(*LG); fill=True
        else: pdf.set_fill_color(255,255,255); fill=False
        for i,c in enumerate(row):
            pdf.cell(widths[i],6.5,c,1,0,"L" if i==0 else "R",fill)
        pdf.ln()
    pdf.ln(2)

pdf=PDF("P","mm","A4"); pdf.set_auto_page_break(True,15); pdf.add_page()
pdf.set_font("Helvetica","B",15); pdf.set_text_color(*NAVY)
pdf.set_x(pdf.l_margin); pdf.multi_cell(0,8,"Bright Autocomp Private Limited");
pdf.set_font("Helvetica","B",13); pdf.set_x(pdf.l_margin); pdf.multi_cell(0,7,"Maximum Withdrawal Plan")
pdf.set_font("Helvetica","I",8.5); pdf.set_text_color(*GREY); pdf.set_x(pdf.l_margin)
pdf.multi_cell(0,5,"How the shareholders extract the maximum amount, tax-efficiently. Based on the actual "
    "audited FY2024-25 balance sheet (figures converted from Rs.'00). Planning note, not tax advice.")
pdf.set_text_color(0,0,0); pdf.ln(2)

h1(pdf,"1. The key point - most of the money is a LOAN, not equity")
body(pdf,"The balance sheet shows Rs.1,54,25,000 as \"Short-term borrowings - loan repayable on demand from "
    "related parties\" (Note 7). This is the shareholders' own money, recorded as a loan to the company "
    "(because the directors differed from the shareholders). The company is the BORROWER; the shareholders "
    "are the LENDERS.")
body(pdf,"Repayment of a genuine loan is simply return of principal - it is NOT income and NOT taxable in the "
    "lender's hands. No dividend, no capital gains. So this Rs.1.54 cr can be withdrawn TAX-FREE, without "
    "liquidation or conversion.",bold=True)

h1(pdf,"2. Withdrawal map - what is tax-free and what is taxed")
table(pdf,[
    ["Amount held for shareholders","Rs.","Tax on withdrawal"],
    ["Loan from related parties (Note 7)",rs(LOAN),"TAX-FREE - loan repayment"],
    ["Paid-up share capital",rs(CAPITAL),"TAX-FREE - return of capital"],
    ["Reserve & Surplus (accumulated profits)",rs(RESERVES),"TAXABLE - dividend / slab"],
    ["TOTAL potentially extractable",rs(LOAN+CAPITAL+RESERVES),""],
], [92,34,64], total_idx=3, green_rows=(0,1))
body(pdf,"Of about %s available to the shareholders, %s (loan + capital) can come out TAX-FREE, and only the "
    "%s of reserves is exposed to tax."%(rs(LOAN+CAPITAL+RESERVES),rs(LOAN+CAPITAL),rs(RESERVES)))

h1(pdf,"3. The real constraint is CASH, not tax")
table(pdf,[
    ["Funding the Rs.1.54 cr loan repayment","Rs."],
    ["Cash & bank balances on hand",rs(CASH)],
    ["Trade receivables (collect)",rs(RECV)],
    ["Fixed deposit",rs(FD)],
    ["Liquid funds available now",rs(LIQUID)],
    ["Loan to be repaid",rs(LOAN)],
    ["Funding gap to arrange",rs(GAP)],
], [126,64], total_idx=5)
body(pdf,"About %s can be repaid straight away from existing cash and receivables. The remaining ~%s must be "
    "funded from ongoing rental/operating income over time, or by monetising the Manesar land (book %s). "
    "Repaying the loan is tax-free; the only tax question is IF the land is SOLD to raise cash - that sale "
    "attracts capital-gains tax on any gain over cost."%(rs(LIQUID),rs(GAP),rs(LAND)))

h1(pdf,"4. Recommended structure")
for s in [
    "Step 1 - Repay ~%s now from cash + receivables (tax-free)."%rs(LIQUID),
    "Step 2 - Fund the balance ~%s from rental/operating cash flows over 1-2 years, so the land need not be "
    "sold and no capital-gains tax arises."%rs(GAP),
    "Step 3 - If the shareholders also want the land value out, convert to an LLP under Sec 47(xiiib) (the "
    "company QUALIFIES - turnover under Rs.60L, assets under Rs.5 cr). The loan carries over to the LLP and "
    "the LLP repays it tax-free; the Rs.51.9L reserves are drawn as interest on capital, remuneration and "
    "tax-free profit share over time.",
    "Avoid liquidation: it would tax the reserves as deemed dividend and the land gain at the company - the "
    "opposite of the goal.",
]: bullet(pdf,s)

h1(pdf,"5. Compliance & risk checks (discuss with your CA)")
for s in [
    "GENUINENESS: the loan must be a bona fide, documented liability (loan confirmations, both parties' "
    "books, and evidence of how the capital came to be recorded as a loan). If that reclassification was "
    "not done through a proper legal mechanism, the tax officer could challenge the repayment. Keep the "
    "paper trail.",
    "Sec 269T: repay a loan of Rs.20,000+ only by account-payee cheque / bank / electronic transfer - NOT "
    "cash - else 100% penalty u/s 271E.",
    "Sec 2(22)(e) does NOT apply here: it deems a dividend when a company LENDS to a shareholder. Here the "
    "shareholders lent to the company; repaying them is outside 2(22)(e).",
    "Interest on the loan is taxable to shareholders at slab and deductible for the company/LLP (within 12% "
    "for a partner loan post-conversion).",
    "Planning note, not tax advice - validate every step with your CA before acting.",
]: bullet(pdf,s)

out=os.path.join(HERE,"Bright_Autocomp_Maximum_Withdrawal_Plan.pdf")
pdf.output(out); print("Wrote",out)
