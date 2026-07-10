#!/usr/bin/env python3
"""
Deterministic fictional data generator for the Customer Success Hub.

100% made-up companies/people — safe to publish. Seeded RNG → re-running gives
the identical dataset, so the template stays reproducible.

Each record's dict keys are the EXACT Lark field names. Link fields are emitted
as a separate `_links` dict ({link_field: [referenced primary value, ...]}) and
resolved to record_ids by seed_data.py.
"""
import random
from datetime import datetime

random.seed(42)
TODAY = datetime(2026, 6, 17)

CSMS = ["Alice Tran", "Brian Le", "Chloe Pham", "David Vu", "Emma Ngo"]
PLAN_ORDER = ["Starter", "Pro", "Business", "Enterprise"]
FEATURES = ["Dashboards", "Automations", "API", "Mobile", "Reports",
            "Integrations", "AI Assistant", "SSO"]
SNAP_MONTHS = [(2026, m) for m in range(1, 7)]  # Jan–Jun 2026
QUARTERS = ["Q1-2026", "Q2-2026", "Q3-2026"]

PREFIXES = ["Nimbus", "Orbit", "Vertex", "Lumen", "Quanta", "Cobalt", "Aster",
            "Pinnacle", "Cedar", "Helix", "Vela", "Onyx", "Magnolia", "Falcon",
            "Beacon", "Harbor", "Summit", "Drift", "Atlas", "Nova", "Ember",
            "Cirrus", "Solstice", "Tidal", "Granite", "Maple", "Zephyr", "Comet",
            "Indigo", "Vantage", "Kestrel", "Lattice", "Mirador", "Polaris",
            "Quill", "Roan", "Sable", "Thalo", "Umbra", "Wren", "Yarrow",
            "Ardent", "Brio", "Cove", "Dune", "Estuary", "Fathom", "Glade",
            "Hollow", "Junction"]
INDUSTRY_SUFFIX = {"Retail": "Retail", "Tech": "Labs", "Finance": "Capital",
                   "Manufacturing": "Industries", "Healthcare": "Health",
                   "Education": "Learning", "Other": "Group"}
INDUSTRIES = list(INDUSTRY_SUFFIX.keys())
REGIONS = ["North America", "EMEA", "APAC", "LATAM"]
PRICE = {"Starter": 8, "Pro": 15, "Business": 25, "Enterprise": 40}


def ms(y, m, d):
    return int(datetime(y, m, d, 12, 0).timestamp() * 1000)


def month_ms(y, m):
    return ms(y, m, 1)


def quarter_of(y, m):
    return f"Q{(m - 1)//3 + 1}-{y}"


def health(util, core, adv, stick, sentiment, tickets):
    return round(0.3*util + 0.25*core + 0.15*adv + 0.1*stick
                 + 0.1*min(sentiment*10, 100) + 0.1*max(0, 100-tickets*10))


def plan_shift(plan, step):
    i = max(0, min(3, PLAN_ORDER.index(plan) + step))
    return PLAN_ORDER[i]


REASONS = [
    ("Price too high", "Price", ["Churn", "Downsell"],
     "Customer perceives ROI does not justify the price at renewal.",
     "Bring ROI/value review + flexible packaging to the renewal call early."),
    ("Switched to competitor", "Competitor", ["Churn"],
     "Customer migrated to a competing product.",
     "Run win-back, competitive battlecard, exec sponsor outreach."),
    ("Low feature adoption", "Adoption", ["Churn", "Downsell"],
     "Core features under-used; product not embedded in workflow.",
     "Adoption plan, enablement sessions, success-plan milestones."),
    ("Budget cut / cost reduction", "Budget", ["Churn", "Downsell"],
     "Customer reducing spend org-wide.",
     "Right-size plan, multi-year discount, prove cost-savings."),
    ("Missing key feature", "Product Gap", ["Churn", "Downsell"],
     "A must-have capability is not available.",
     "Log product feedback, share roadmap, propose workaround."),
    ("Poor support experience", "Support", ["Churn"],
     "Unresolved tickets / slow response eroded trust.",
     "Service recovery plan, dedicated support, exec apology."),
    ("Champion left / sponsor change", "Business Change", ["Churn", "Downsell"],
     "Key champion departed; new stakeholder not bought-in.",
     "Multi-thread relationships, re-onboard new sponsor fast."),
    ("M&A / company restructure", "Business Change", ["Churn"],
     "Acquisition or restructure changed tooling decisions.",
     "Map new org, find new entry point, consolidate contracts."),
    ("Seat reduction / downsizing", "Budget", ["Downsell"],
     "Headcount reduction lowers seat need.",
     "Protect price-per-seat, add modules to offset seat loss."),
    ("Onboarding / time-to-value too slow", "Adoption", ["Churn"],
     "Customer never reached first value.",
     "Accelerated onboarding, TTV milestones, hands-on setup."),
]


def gen_reasons():
    return [{"Reason": r[0], "Category": r[1], "Applies To": r[2],
             "Description": r[3], "Mitigation Playbook": r[4]} for r in REASONS]


def gen_accounts():
    n = 50
    segments = (["Enterprise"] * 12 + ["Mid-Market"] * 20 + ["SMB"] * 18)
    statuses = (["Onboarding"] * 4 + ["At Risk"] * 6 + ["Churned"] * 5 + ["Active"] * 35)
    random.shuffle(segments)
    random.shuffle(statuses)

    accounts = []
    for i in range(n):
        seg = segments[i]
        status = statuses[i]
        industry = random.choice(INDUSTRIES)
        name = f"{PREFIXES[i]} {INDUSTRY_SUFFIX[industry]}"
        csm = CSMS[i % 5]                      # ~10 accounts per CSM
        if seg == "Enterprise":
            plan = random.choice(["Enterprise", "Enterprise", "Business"])
            seats = random.randint(200, 1200)
        elif seg == "Mid-Market":
            plan = random.choice(["Business", "Business", "Pro"])
            seats = random.randint(50, 300)
        else:
            plan = random.choice(["Pro", "Starter", "Starter"])
            seats = random.randint(5, 60)
        price = round(PRICE[plan] * random.uniform(0.85, 1.15))
        arr = seats * price * 12

        if status == "Onboarding":
            sd = random.randint(1, 4)
        else:
            sd = random.randint(7, 40)
        start = datetime(TODAY.year, TODAY.month, 15)
        sy = TODAY.year - (sd // 12)
        sm = TODAY.month - (sd % 12)
        if sm <= 0:
            sm += 12
            sy -= 1
        start_ms = ms(sy, sm, 15)

        if status == "Churned":
            ry, rm = 2026, random.randint(1, 5)
            forecast = "Churn Risk"
        elif status == "Onboarding":
            ry, rm = 2027, random.randint(1, 4)
            forecast = "Undecided"
        elif status == "At Risk":
            ry, rm = (2026, random.randint(7, 12))
            forecast = random.choice(["Churn Risk", "Churn Risk", "Downsell"])
        else:  # Active
            if random.random() < 0.7:
                ry, rm = (2026, random.randint(7, 12)) if random.random() < .6 else (2027, random.randint(1, 3))
                forecast = "Renew"
            else:
                ry, rm = (2026, random.randint(8, 12))
                forecast = "Upsell"

        accounts.append({
            "_status": status, "_csm": csm, "_plan": plan, "_arr": arr,
            "Account Name": name, "Account ID": f"ACC-{i+1:03d}",
            "Segment": seg, "Industry": industry, "Region": random.choice(REGIONS),
            "CSM Owner": csm, "Plan": plan, "Seats": seats,
            "Price per Seat (USD)": price, "ARR (USD)": arr, "Status": status,
            "Start Date": start_ms, "Next Renewal Date": ms(ry, rm, random.randint(2, 27)),
            "Renewal Forecast": forecast,
            "Notes": f"{seg} {industry} account managed by {csm}.",
        })
    return accounts


def gen_snapshots(accounts):
    """6 monthly snapshots per non-churned account (4 declining for churned).
    Mutates each account with Current/Avg health + Last Snapshot."""
    snaps = []
    for acc in accounts:
        name, seats, status = acc["Account Name"], acc["Seats"], acc["_status"]
        months = SNAP_MONTHS if status != "Churned" else SNAP_MONTHS[:4]
        healths = []
        for k, (y, m) in enumerate(months):
            t = k / 5.0
            if status == "Active":
                util = random.randint(65, 92) + round(4*t)
                core = util - random.randint(0, 14)
                adv = random.randint(35, 70)
                stick = random.randint(45, 80)
                sent = random.randint(7, 9)
                tix = random.randint(0, 3)
                fcount = random.randint(4, 6)
            elif status == "At Risk":
                util = round(62 - 30*t) + random.randint(-4, 4)
                core = round(55 - 28*t) + random.randint(-4, 4)
                adv = random.randint(8, 28)
                stick = round(45 - 18*t)
                sent = max(2, round(6 - 2*t)) + random.randint(-1, 1)
                tix = round(3 + 5*t) + random.randint(0, 2)
                fcount = random.randint(1, 3)
            elif status == "Onboarding":
                util = round(20 + 40*t) + random.randint(-3, 3)
                core = round(15 + 38*t)
                adv = round(5 + 22*t)
                stick = round(20 + 28*t)
                sent = round(6 + 2*t)
                tix = random.randint(1, 4)
                fcount = random.randint(2, 3)
            else:  # Churned — sharp decline
                util = round(52 - 34*t)
                core = round(45 - 33*t)
                adv = random.randint(5, 18)
                stick = round(40 - 26*t)
                sent = max(1, round(5 - 3*t))
                tix = round(4 + 6*t)
                fcount = random.randint(1, 2)
            util = max(2, min(100, util)); core = max(1, min(100, core))
            stick = max(1, min(100, stick)); sent = max(0, min(10, sent))
            active_users = max(1, round(seats * util / 100))
            h = health(util, core, adv, stick, sent, tix)
            healths.append(h)
            snaps.append({
                "Snapshot": f"{name} {y}-{m:02d}",
                "Month": month_ms(y, m), "Active Users": active_users,
                "License Utilization %": util, "Logins": active_users * random.randint(8, 25),
                "Core Feature Adoption %": core, "Advanced Feature Adoption %": adv,
                "Features Used": random.sample(FEATURES, fcount),
                "Stickiness DAU-MAU %": stick, "Sentiment 0-10": sent,
                "Support Tickets": tix,
                "_links": {"Account": [name]},
            })
        last_y, last_m = months[-1]
        acc["Current Health Score"] = healths[-1]
        acc["Avg Health 6mo"] = round(sum(healths) / len(healths))
        acc["Last Snapshot"] = month_ms(last_y, last_m)
    return snaps


def gen_renewals(accounts, reason_names):
    rens = []
    for acc in accounts:
        name, plan, arr = acc["Account Name"], acc["_plan"], acc["_arr"]
        status, fc = acc["_status"], acc["Renewal Forecast"]
        rdate = acc["Next Renewal Date"]
        ryear = datetime.fromtimestamp(rdate / 1000).year
        rname = f"{name} — {ryear} Renewal"
        reason = None
        if status == "Churned":
            forecast, outcome, prob = "Churn", "Lost-Churn", 20
            pplan, parr = plan, 0
            reason = random.choice([r for r in reason_names if r != "Seat reduction / downsizing"])
        elif fc == "Upsell":
            forecast, outcome, prob = "Upsell", "Pending", 60
            pplan, parr = plan_shift(plan, 1), round(arr * random.uniform(1.15, 1.45))
        elif fc == "Downsell":
            forecast, outcome, prob = "Downsell", "Pending", 50
            pplan, parr = plan_shift(plan, -1), round(arr * random.uniform(0.6, 0.85))
            reason = "Seat reduction / downsizing"
        elif fc == "Churn Risk":
            forecast, outcome, prob = "Churn", "Pending", 30
            pplan, parr = plan, round(arr * random.uniform(0.0, 0.6))
            reason = random.choice(reason_names)
        elif fc == "Undecided":
            forecast, outcome, prob = "Pre-Renewal", "Pending", 65
            pplan, parr = plan, arr
        else:  # Renew
            forecast = random.choice(["Pre-Renewal", "In Negotiation"])
            outcome, prob = "Pending", 80
            pplan, parr = plan, round(arr * random.uniform(1.0, 1.06))
        rec = {
            "Renewal Name": rname, "Renewal Date": rdate, "Current Plan": plan,
            "Current ARR (USD)": arr, "Proposed Plan": pplan, "Proposed ARR (USD)": parr,
            "Forecast": forecast, "Probability %": prob, "Outcome": outcome,
            "Owner": acc["_csm"],
            "Notes": f"{forecast} forecast for {name}.",
            "_links": {"Account": [name]},
            "_renewal_name": rname,
        }
        if reason:
            rec["_links"]["Reason"] = [reason]
        rens.append(rec)
    return rens


def _mdate(y, m):
    return ms(y, m, random.randint(2, 27))


def gen_movements(accounts, reason_names):
    """~120 ARR events across the last 12 months (2025-07 … 2026-06)."""
    window = [(2025, m) for m in range(7, 13)] + [(2026, m) for m in range(1, 7)]
    movs = []

    def add(acc, etype, before, after, plan_from, plan_to, reason=None, link_ren=None):
        y, m = random.choice(window)
        nm = f"{acc['Account Name']} — {etype} — {y}-{m:02d}"
        rec = {"Movement": nm, "Event Type": etype, "Event Date": _mdate(y, m),
               "ARR Before (USD)": before, "ARR After (USD)": after,
               "Owner": acc["_csm"], "_links": {"Account": [acc["Account Name"]]},
               "Notes": ""}
        if plan_from:
            rec["Plan From"] = plan_from
        if plan_to:
            rec["Plan To"] = plan_to
        if reason:
            rec["_links"]["Reason"] = [reason]
        if link_ren:
            rec["_links"]["Linked Renewal"] = [link_ren]
        movs.append(rec)

    active = [a for a in accounts if a["_status"] in ("Active", "Onboarding")]
    at_risk = [a for a in accounts if a["_status"] == "At Risk"]
    churned = [a for a in accounts if a["_status"] == "Churned"]

    # New (acquisition) — 20
    for a in random.sample(accounts, 20):
        add(a, "New", 0, round(a["_arr"] * random.uniform(0.7, 1.0)), None, a["_plan"])
    # Upsell — 40
    for a in random.sample(active, min(40, len(active))) + random.sample(active, max(0, 40 - len(active))):
        before = round(a["_arr"] * random.uniform(0.6, 0.85))
        add(a, "Upsell", before, round(before * random.uniform(1.15, 1.5)),
            a["_plan"], plan_shift(a["_plan"], random.choice([0, 1])))
    # Renewal-Won (flat) — 30
    for a in random.sample(active, min(30, len(active))):
        add(a, "Renewal-Won", a["_arr"], round(a["_arr"] * random.uniform(1.0, 1.05)),
            a["_plan"], a["_plan"],
            link_ren=f"{a['Account Name']} — {datetime.fromtimestamp(a['Next Renewal Date']/1000).year} Renewal")
    # Downsell — 15 (some at-risk + some active)
    for a in (at_risk + random.sample(active, 10)):
        if len([m for m in movs if m["Event Type"] == "Downsell"]) >= 15:
            break
        add(a, "Downsell", a["_arr"], round(a["_arr"] * random.uniform(0.55, 0.8)),
            a["_plan"], plan_shift(a["_plan"], -1), reason=random.choice(reason_names))
    # Churn — 5
    for a in churned:
        add(a, "Churn", a["_arr"], 0, a["_plan"], None,
            reason=random.choice([r for r in reason_names]),
            link_ren=f"{a['Account Name']} — {datetime.fromtimestamp(a['Next Renewal Date']/1000).year} Renewal")
    # Reactivation — 3
    for a in random.sample(active, 3):
        add(a, "Reactivation", 0, round(a["_arr"] * random.uniform(0.5, 0.8)), None, a["_plan"])
    return movs


def gen_activities(accounts):
    acts = []
    types = ["QBR", "Check-in", "Onboarding", "Renewal Call", "Upsell Pitch"]
    for a in random.sample(accounts, 24):
        name, csm, status = a["Account Name"], a["_csm"], a["_status"]
        t = "Onboarding" if status == "Onboarding" else random.choice(types)
        y, m = random.choice([(2026, 4), (2026, 5), (2026, 6), (2026, 7)])
        past = (y, m) <= (2026, 6)
        st = "Done" if past else "Planned"
        rec = {"Activity": f"{t} — {name}", "Type": t, "Date": _mdate(y, m),
               "Owner": csm, "Status": st,
               "Outcome / Next Steps": f"{t} with {name}; follow-up logged.",
               "_links": {"Account": [name]}}
        if t in ("Renewal Call", "Upsell Pitch"):
            rec["_links"]["Related Renewal"] = [
                f"{name} — {datetime.fromtimestamp(a['Next Renewal Date']/1000).year} Renewal"]
        acts.append(rec)
    # escalations for at-risk
    for a in [x for x in accounts if x["_status"] == "At Risk"]:
        acts.append({"Activity": f"Escalation — {a['Account Name']}", "Type": "Escalation",
                     "Date": ms(2026, 6, random.randint(1, 16)), "Owner": a["_csm"],
                     "Status": "Overdue",
                     "Outcome / Next Steps": "Health red — exec escalation + save plan.",
                     "_links": {"Account": [a["Account Name"]]}})
    return acts


def gen_targets(accounts):
    targets = []
    for csm in CSMS:
        book_accts = [a for a in accounts if a["_csm"] == csm and a["_status"] != "Churned"]
        book = sum(a["_arr"] for a in book_accts)
        n = len(book_accts)
        for q in QUARTERS:
            grr_rate = random.uniform(0.92, 0.99)         # retained
            exp_rate = random.uniform(0.08, 0.18)         # expansion
            renewal_actual = round(book * grr_rate)
            expansion_actual = round(book * exp_rate)
            renewal_target = round(book * random.uniform(0.93, 0.97))
            expansion_target = round(book * 0.12)
            grr_actual = round(grr_rate * 100)
            nrr_actual = round((grr_rate + exp_rate) * 100)
            targets.append({
                "Target Key": f"{q} — {csm.split()[0]}", "CSM Owner": csm, "Quarter": q,
                "Portfolio Accounts": n, "Book of Business ARR (USD)": book,
                "Renewal Target ARR (USD)": renewal_target,
                "Renewal Actual ARR (USD)": renewal_actual,
                "Expansion Target ARR (USD)": expansion_target,
                "Expansion Actual ARR (USD)": expansion_actual,
                "GRR Target %": 95, "GRR Actual %": grr_actual,
                "NRR Target %": 110, "NRR Actual %": nrr_actual,
            })
    return targets


def generate():
    accounts = gen_accounts()
    reasons = gen_reasons()
    reason_names = [r["Reason"] for r in reasons]
    snapshots = gen_snapshots(accounts)            # mutates accounts (health)
    renewals = gen_renewals(accounts, reason_names)
    movements = gen_movements(accounts, reason_names)
    activities = gen_activities(accounts)
    targets = gen_targets(accounts)
    # strip private keys from accounts
    clean_accounts = [{k: v for k, v in a.items() if not k.startswith("_")} for a in accounts]
    return {
        "Churn & Downsell Reasons": reasons,
        "Accounts": clean_accounts,
        "Renewals": renewals,
        "Usage Snapshots": snapshots,
        "Revenue Movements": movements,
        "CSM Activities": activities,
        "Commercial Targets": targets,
    }


if __name__ == "__main__":
    data = generate()
    for k, v in data.items():
        print(f"{k:28s} {len(v)} records")
