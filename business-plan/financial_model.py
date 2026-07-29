#!/usr/bin/env python3
"""HealthSnap 3-year financial model — generates consistent tables (MD + CSV).

All amounts in INR unless noted. FX: Rs 95 = $1.
Price points are GST-inclusive consumer prices; net revenue = price / 1.18
once GST registration applies (assumed from month 13; Y1 gross stays under
the Rs 20 lakh service-tax registration threshold in base case).
"""
import csv, io

FX = 95.0

# ---------------- Assumptions ----------------
A = dict(
    # pricing (consumer, GST-inclusive)
    price_pro_m=149, price_pro_y=999, price_fam_m=249, price_fam_y=1999,
    # paying-subscriber mix
    mix_pro_m=0.60, mix_pro_y=0.25, mix_fam=0.15,
    # funnel
    free_per_paid=6.0,          # free active users per paying subscriber
    monthly_churn=0.06,         # paying churn / month (UPI mandate failures included)
    # unit costs / paying user / month
    ai_cost_paid=15.0,          # GPT-4o low-detail + dish-cache (Rs)
    ai_cost_free=2.5,           # capped 3 photos/day, low detail (Rs)
    rzp_fee=0.0236,             # 2% + 18% GST on the fee
    vapi_cost_fam=25.0,         # Pooja voice minutes, Family subs only (Rs)
    # CAC per gross-added paying subscriber
    cac=[200, 300, 350],        # Y1 (founder-led/organic heavy), Y2, Y3
    # fixed infra Rs/month by year (n8n Pro, Supabase Pro, Netlify, domain, tools)
    infra=[11_000, 22_000, 40_000],
    # people/ops Rs/month by year (support VA, part-time dietitian for DB, content)
    people=[15_000, 60_000, 150_000],
    # one-time build (native Android app Y2)
    one_time={13: 250_000},
)

# blended ARPU (gross, GST-inclusive) per paying sub / month
arpu = (A['mix_pro_m'] * A['price_pro_m'] +
        A['mix_pro_y'] * A['price_pro_y'] / 12 +
        A['mix_fam'] * (0.7 * A['price_fam_m'] + 0.3 * A['price_fam_y'] / 12))

# ---------------- Subscriber paths (paying subs, end of month) ----------------
# gross adds per month by year-phase; churn applied on opening base
def build_path(adds_by_month):
    subs, rows = 0.0, []
    for m in range(1, 37):
        churned = subs * A['monthly_churn']
        adds = adds_by_month(m)
        subs = subs - churned + adds
        rows.append((m, adds, churned, subs))
    return rows

def base_adds(m):
    if m <= 3:  return 25 + 15 * (m - 1)      # 25,40,55 — founder network + first reels
    if m <= 12: return 60 + 22 * (m - 4)      # ramp to ~236/mo as influencer engine scales
    if m <= 24: return 260 + 30 * (m - 13)    # Y2: Play Store + paid ads
    return 620 + 45 * (m - 25)                # Y3: scale + family plans push

def cons_adds(m):  return base_adds(m) * 0.5
def amb_adds(m):   return base_adds(m) * 1.8

def year_of(m): return (m - 1) // 12  # 0,1,2

def pnl(path):
    """monthly P&L rows"""
    out = []
    for (m, adds, churned, subs) in path:
        y = year_of(m)
        gross_rev = subs * arpu
        gst_reg = m > 12                      # base case: register from Y2
        gst = gross_rev - gross_rev / 1.18 if gst_reg else 0.0
        net_rev = gross_rev - gst
        rzp = gross_rev * A['rzp_fee']
        free_users = subs * A['free_per_paid']
        ai = subs * A['ai_cost_paid'] + free_users * A['ai_cost_free']
        vapi = subs * A['mix_fam'] * A['vapi_cost_fam']
        infra = A['infra'][y]
        mkt = adds * A['cac'][y]
        people = A['people'][y]
        one = A['one_time'].get(m, 0)
        total_cost = rzp + ai + vapi + infra + mkt + people + one
        ebitda = net_rev - total_cost
        out.append(dict(m=m, adds=adds, churned=churned, subs=subs, free=free_users,
                        gross=gross_rev, gst=gst, net=net_rev, rzp=rzp, ai=ai, vapi=vapi,
                        infra=infra, mkt=mkt, people=people, one=one, cost=total_cost,
                        ebitda=ebitda))
    return out

def annual(rows):
    ys = []
    for y in range(3):
        yr = rows[y*12:(y+1)*12]
        agg = {k: sum(r[k] for r in yr) for k in
               ('adds','churned','gross','gst','net','rzp','ai','vapi','infra','mkt','people','one','cost','ebitda')}
        agg['subs_end'] = yr[-1]['subs']
        agg['free_end'] = yr[-1]['free']
        ys.append(agg)
    return ys

def fmt(n, dec=0):
    return f"{n:,.{dec}f}"

def lakh(n):
    return f"{n/100000:,.1f}"

base = pnl(build_path(base_adds))
cons = pnl(build_path(cons_adds))
amb  = pnl(build_path(amb_adds))

print(f"Blended gross ARPU/paying sub/month: Rs {arpu:.0f}")
print()

# unit economics
ue_net = arpu / 1.18
ue_var = A['ai_cost_paid'] + A['free_per_paid'] * A['ai_cost_free'] + arpu * A['rzp_fee'] + A['mix_fam'] * A['vapi_cost_fam']
cm = ue_net - ue_var
avg_life = 1 / A['monthly_churn']
ltv = cm * avg_life
print(f"Net ARPU (ex-GST): Rs {ue_net:.0f}")
print(f"Variable cost/sub/mo (AI paid+free share, Razorpay, VAPI): Rs {ue_var:.0f}")
print(f"Contribution margin/sub/mo: Rs {cm:.0f}  ({cm/ue_net*100:.0f}%)")
print(f"Avg subscriber life at {A['monthly_churn']*100:.0f}% churn: {avg_life:.1f} months")
print(f"LTV: Rs {ltv:.0f}   LTV:CAC (Y2 CAC 350): {ltv/350:.1f}:1")
print()

# break-even month (base)
be = next((r['m'] for r in base if r['ebitda'] > 0), None)
cum = 0; be_cash = None; trough = 0; trough_m = 0
for r in base:
    cum += r['ebitda']
    if cum < trough: trough, trough_m = cum, r['m']
    if be_cash is None and cum > 0: be_cash = r['m']
print(f"Base case: first EBITDA-positive month: M{be}; cumulative cash-positive: M{be_cash}")
print(f"Peak funding need (cumulative trough): Rs {fmt(-trough)} at M{trough_m}")
print()

# ---- Year-1 monthly table (base) ----
print("YEAR-1 MONTHLY (BASE) — Rs")
hdr = "| Month | Adds | Churn | Paying subs | Free users | Gross revenue | AI cost | Razorpay | Infra | Marketing | People | EBITDA |"
print(hdr); print("|" + "---|" * 12)
for r in base[:12]:
    print(f"| M{r['m']} | {r['adds']:.0f} | {r['churned']:.0f} | {r['subs']:.0f} | {r['free']:.0f} | "
          f"{fmt(r['gross'])} | {fmt(r['ai'])} | {fmt(r['rzp'])} | {fmt(r['infra'])} | {fmt(r['mkt'])} | {fmt(r['people'])} | {fmt(r['ebitda'])} |")
print()

# ---- 3-year annual (all scenarios) ----
for name, rows in (("CONSERVATIVE", cons), ("BASE", base), ("AMBITIOUS", amb)):
    ys = annual(rows)
    print(f"3-YEAR ANNUAL — {name} (Rs lakh)")
    print("| Line | Y1 | Y2 | Y3 |")
    print("|---|---|---|---|")
    def row(lbl, key, sign=1):
        print(f"| {lbl} | {lakh(sign*ys[0][key])} | {lakh(sign*ys[1][key])} | {lakh(sign*ys[2][key])} |")
    print(f"| Paying subs (year-end) | {fmt(ys[0]['subs_end'])} | {fmt(ys[1]['subs_end'])} | {fmt(ys[2]['subs_end'])} |")
    print(f"| Free users (year-end) | {fmt(ys[0]['free_end'])} | {fmt(ys[1]['free_end'])} | {fmt(ys[2]['free_end'])} |")
    row("Gross revenue", 'gross')
    row("Less GST (output)", 'gst')
    row("Net revenue", 'net')
    row("AI / vision cost", 'ai')
    row("Payment fees", 'rzp')
    row("Voice (VAPI)", 'vapi')
    row("Infrastructure", 'infra')
    row("Marketing", 'mkt')
    row("People & ops", 'people')
    row("One-time build", 'one')
    row("Total costs", 'cost')
    row("EBITDA", 'ebitda')
    print()

# ---- CSV export ----
with open('/home/user/anthropic-finance/business-plan/financial-model.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(["HealthSnap 3-year monthly financial model (BASE case). All Rs. FX Rs95/$."])
    w.writerow(["Assumptions:", f"ARPU Rs{arpu:.0f} gross", f"churn {A['monthly_churn']*100:.0f}%/mo",
                f"AI Rs{A['ai_cost_paid']}/paid +Rs{A['ai_cost_free']}/free user", f"CAC {A['cac']}",
                f"free:paid {A['free_per_paid']}", "GST 18% from M13"])
    w.writerow([])
    w.writerow(["Month","Gross adds","Churned","Paying subs (EOM)","Free users","Gross revenue","GST",
                "Net revenue","AI cost","Payment fees","VAPI","Infra","Marketing","People","One-time",
                "Total cost","EBITDA","Cumulative EBITDA"])
    cum = 0
    for r in base:
        cum += r['ebitda']
        w.writerow([r['m'], round(r['adds']), round(r['churned']), round(r['subs']), round(r['free']),
                    round(r['gross']), round(r['gst']), round(r['net']), round(r['ai']), round(r['rzp']),
                    round(r['vapi']), r['infra'], round(r['mkt']), r['people'], r['one'],
                    round(r['cost']), round(r['ebitda']), round(cum)])
print("CSV written.")
