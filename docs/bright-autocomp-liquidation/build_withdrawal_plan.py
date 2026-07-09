#!/usr/bin/env python3
"""
Bright Autocomp Private Limited — MAXIMUM WITHDRAWAL PLAN.

Objective: get the maximum money out to the shareholders, most of which sits in
the books as a Rs.1.54 cr "loan repayable on demand from related parties"
(shareholders' funds recorded as a loan because directors differed from
shareholders).

Key tax insight: repayment of a GENUINE loan = return of principal = NOT taxable.
So the Rs.1.54 cr can be withdrawn tax-free; only the Rs.51.9L reserves attract tax.
Builds a Word plan. Planning model, not tax advice.
"""
from docx import Document
from docx.shared import Pt, RGBColor
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- actual figures (x100 from Rs.'00) ----
CAPITAL   = 1000.00   * 100      # 1,00,000
RESERVES  = 51896.68  * 100      # 51,89,668
LOAN_RP   = 154250.00 * 100      # 1,54,25,000  loan from related parties (shareholders)
LT_BORROW = 1820.00   * 100      # 1,82,000
PAYABLES  = 126.57    * 100
OTHER_CL  = 275.24    * 100
PROVIS    = 1160.83   * 100
CASH      = 61761.95  * 100      # 61,76,195
RECV      = 2774.60   * 100      # 2,77,460
FD        = 244.30    * 100      # 24,430
LAND      = 145748.47 * 100      # 1,45,74,847

OTHER_CREDITORS = LT_BORROW + PAYABLES + OTHER_CL + PROVIS
LIQUID_NOW = CASH + RECV + FD
GAP = LOAN_RP - LIQUID_NOW

def money(x): return u"₹ {:,.0f}".format(round(x))

doc = Document()
doc.add_heading("Bright Autocomp Private Limited — Maximum Withdrawal Plan", 0)
p = doc.add_paragraph()
run = p.add_run("How the shareholders extract the maximum amount, tax-efficiently. Based on the actual "
                "audited FY2024-25 balance sheet (figures converted from Rs.'00). Planning note, not tax advice.")
run.italic = True; run.font.size = Pt(9)

doc.add_heading("1. The key point — most of the money is a LOAN, not equity", 1)
doc.add_paragraph(
    "The balance sheet shows Rs.1,54,25,000 as \"Short-term borrowings — loan repayable on demand from "
    "related parties\" (Note 7). This is the shareholders' own money, recorded as a loan to the company "
    "(because the directors differed from the shareholders). The company is the BORROWER; the shareholders "
    "are the LENDERS.")
q = doc.add_paragraph()
qr = q.add_run("Repayment of a genuine loan is simply return of principal — it is NOT income and NOT taxable "
               "in the lender's hands. No dividend, no capital gains. So this Rs.1.54 cr can be withdrawn "
               "TAX-FREE, without liquidation or conversion.")
qr.bold = True

doc.add_heading("2. Withdrawal map — what is tax-free and what is taxed", 1)
t = doc.add_table(rows=1, cols=3); t.style = "Light Grid Accent 1"
h = t.rows[0].cells
h[0].text = "Amount held for shareholders"; h[1].text = "Rs."; h[2].text = "Tax on withdrawal"
for lab, val, tax in [
    ("Loan from related parties (Note 7)", LOAN_RP, "TAX-FREE — repayment of principal"),
    ("Paid-up share capital", CAPITAL, "TAX-FREE — return of capital (= cost)"),
    ("Reserve & Surplus (accumulated profits)", RESERVES, "TAXABLE — dividend/slab (or drawn via LLP over time)"),
    ("TOTAL potentially extractable", LOAN_RP + CAPITAL + RESERVES, ""),
]:
    c = t.add_row().cells; c[0].text = lab; c[1].text = money(val); c[2].text = tax
doc.add_paragraph(
    "So of roughly {} available to the shareholders, {} (the loan + capital) can come out TAX-FREE, and "
    "only the {} of reserves is exposed to tax."
    .format(money(LOAN_RP + CAPITAL + RESERVES), money(LOAN_RP + CAPITAL), money(RESERVES)))

doc.add_heading("3. The real constraint is CASH, not tax", 1)
t2 = doc.add_table(rows=1, cols=2); t2.style = "Light Grid Accent 1"
t2.rows[0].cells[0].text = "Funding the Rs.1.54 cr loan repayment"; t2.rows[0].cells[1].text = "Rs."
for lab, val in [
    ("Cash & bank balances on hand", CASH),
    ("Trade receivables (collect)", RECV),
    ("Fixed deposit", FD),
    ("Liquid funds available now", LIQUID_NOW),
    ("Loan to be repaid", LOAN_RP),
    ("Funding gap to arrange", GAP),
]:
    c = t2.add_row().cells; c[0].text = lab; c[1].text = money(val)
doc.add_paragraph(
    "About {} can be repaid straight away from existing cash and receivables. The remaining ~{} has to be "
    "funded either from ongoing rental/operating income over time, or by monetising the Manesar land "
    "(book {}). Repaying the loan itself is tax-free; the only tax question is IF the land is SOLD to raise "
    "cash — that sale would attract capital-gains tax on any gain over cost."
    .format(money(LIQUID_NOW), money(GAP), money(LAND)))

doc.add_heading("4. Recommended structure", 1)
for s in [
    "Step 1 — Repay the loan from available liquidity now: pay out ~{} to the shareholders immediately from "
    "cash + receivables (tax-free).".format(money(LIQUID_NOW)),
    "Step 2 — Fund the balance ~{} from rental/operating cash flows over the next 1-2 years, so the land "
    "need not be sold and no capital-gains tax arises.".format(money(GAP)),
    "Step 3 — If the shareholders also want the land value out, convert the company to an LLP under Sec "
    "47(xiiib) (the company QUALIFIES — turnover under Rs.60L, assets under Rs.5 cr). The loan carries over "
    "to the LLP and the LLP repays it tax-free; the Rs.51.9L reserves are then drawn as interest on capital, "
    "remuneration and tax-free profit share over time.",
    "Avoid liquidation: it would tax the reserves as deemed dividend and the land gain at the company — the "
    "opposite of the goal.",
]:
    doc.add_paragraph(s, style="List Bullet")

doc.add_heading("5. Compliance & risk checks (discuss with your CA)", 1)
for s in [
    "GENUINENESS: the loan must be a bona fide, documented liability (loan confirmation, both parties' books, "
    "how the capital came to be recorded as a loan). If the reclassification of shareholders' funds into a "
    "loan was not done through a proper legal mechanism, the tax officer could challenge the repayment. Keep "
    "the paper trail.",
    "Sec 269T: repayment of a loan of Rs.20,000 or more must be by account-payee cheque / bank / electronic "
    "transfer — NOT cash — else 100% penalty u/s 271E.",
    "Sec 2(22)(e) does NOT apply here: that deems a dividend when a company LENDS to a shareholder. Here the "
    "shareholders lent to the company; repaying them is outside 2(22)(e).",
    "Interest paid on the loan is taxable to the shareholders at slab and deductible for the company/LLP "
    "(within 12% for a partner loan post-conversion).",
    "This is a planning note, not tax advice — validate every step with your CA before acting.",
]:
    doc.add_paragraph(s, style="List Bullet")

out = os.path.join(HERE, "Bright_Autocomp_Maximum_Withdrawal_Plan.docx")
doc.save(out)
print("Wrote", out)
print("\n--- SUMMARY ---")
print("Loan (tax-free):", money(LOAN_RP))
print("Capital (tax-free):", money(CAPITAL))
print("Reserves (taxable):", money(RESERVES))
print("Liquid now:", money(LIQUID_NOW), " Gap:", money(GAP))
