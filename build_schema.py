#!/usr/bin/env python3
"""
Customer Success Hub — Lark Base schema builder.

Idempotent + re-runnable: creates a new Bitable app the first time, persists all
ids to base_ids.json, and on re-run reuses what already exists (skips tables /
fields already created). Re-running on a *fresh* machine produces a brand-new
copy of the template — this is the "duplicate-able" mechanism (goal #1).

Uses the lark-cli `api` passthrough.
"""
import subprocess, json, sys, os, time, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
IDS_PATH = os.path.join(HERE, "base_ids.json")


def _resolve_cli():
    """Find the Lark CLI on this machine (portable across users)."""
    for probe in (["lark-cli"], ["lark"], ["npx", "--no-install", "@larksuite/cli"]):
        if shutil.which(probe[0]):
            return probe
    return ["npx", "--no-install", "@larksuite/cli"]


LARK_CLI_BIN = _resolve_cli()

# ── Lark Bitable field type ids ──
TEXT = 1; NUMBER = 2; SINGLE = 3; MULTI = 4; DATE = 5; FORMULA = 20; BILINK = 21

CSMS = ["Alice Tran", "Brian Le", "Chloe Pham", "David Vu", "Emma Ngo"]
PLANS = ["Starter", "Pro", "Business", "Enterprise"]
QUARTERS = ["Q1-2026", "Q2-2026", "Q3-2026"]


# ───────────────────────── CLI helper ─────────────────────────
def lark(method, path, data=None, params=None, allow_fail=False):
    cmd = LARK_CLI_BIN + ["api", method, path, "--as", "user"]
    if data:
        cmd += ["--data", json.dumps(data, ensure_ascii=False)]
    if params:
        cmd += ["--params", json.dumps(params)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    raw = r.stdout if r.stdout.strip() else r.stderr
    idx = raw.find("{")
    if idx > 0:
        raw = raw[idx:]
    try:
        resp = json.loads(raw)
    except Exception:
        print(f"[PARSE ERR] {method} {path}\n  stdout={r.stdout[:200]}\n  stderr={r.stderr[:200]}")
        if not allow_fail:
            sys.exit(1)
        return None
    if resp.get("code", -1) != 0:
        if allow_fail:
            return None
        print(f"[API ERR] {method} {path}\n{json.dumps(resp, ensure_ascii=False, indent=2)[:600]}")
        sys.exit(1)
    time.sleep(0.12)  # gentle throttle
    return resp.get("data")


def sel(*opts):
    return {"options": [{"name": o} for o in opts]}


# ───────────────────────── id persistence ─────────────────────────
def load_ids():
    if os.path.exists(IDS_PATH):
        with open(IDS_PATH) as f:
            return json.load(f)
    return {"app_token": None, "tables": {}, "fields": {}}


def save_ids(ids):
    with open(IDS_PATH, "w") as f:
        json.dump(ids, f, ensure_ascii=False, indent=2)


# ───────────────────────── app / table / field ops ─────────────────────────
def get_or_create_app(ids):
    if ids.get("app_token"):
        print(f"• Reusing app {ids['app_token']}")
        return ids["app_token"]
    data = lark("POST", "/open-apis/bitable/v1/apps",
                {"name": "Customer Success Hub", "time_zone": "Asia/Shanghai"})
    token = data["app"]["app_token"]
    ids["app_token"] = token
    ids["url"] = data["app"].get("url", f"https://open.larksuite.com/base/{token}")
    save_ids(ids)
    print(f"✓ Created app {token}")
    return token


def list_tables(app):
    data = lark("GET", f"/open-apis/bitable/v1/apps/{app}/tables", params={"page_size": 100})
    return data.get("items", [])


def list_fields(app, tid):
    data = lark("GET", f"/open-apis/bitable/v1/apps/{app}/tables/{tid}/fields",
                params={"page_size": 200})
    return data.get("items", [])


def setup_first_table(app, ids, name, primary):
    """Reuse the auto-created default table as the first (Accounts) table."""
    if name in ids["tables"]:
        return ids["tables"][name]
    tables = list_tables(app)
    tid = tables[0]["table_id"]
    lark("PATCH", f"/open-apis/bitable/v1/apps/{app}/tables/{tid}", {"name": name})
    ids["tables"][name] = tid
    save_ids(ids)
    print(f"✓ Default table → '{name}' ({tid})")
    clean_default_fields(app, tid, primary)
    return tid


def get_or_create_table(app, ids, name, primary):
    if name in ids["tables"]:
        return ids["tables"][name]
    for t in list_tables(app):
        if t["name"] == name:
            ids["tables"][name] = t["table_id"]
            save_ids(ids)
            return t["table_id"]
    data = lark("POST", f"/open-apis/bitable/v1/apps/{app}/tables", {"table": {"name": name}})
    tid = data["table_id"]
    ids["tables"][name] = tid
    save_ids(ids)
    print(f"✓ Created table '{name}' ({tid})")
    clean_default_fields(app, tid, primary)
    return tid


def clean_default_fields(app, tid, primary_name):
    """Rename the primary field; delete every other auto-created field. Runs once at create."""
    for f in list_fields(app, tid):
        if f.get("is_primary"):
            if f["field_name"] != primary_name:
                lark("PUT", f"/open-apis/bitable/v1/apps/{app}/tables/{tid}/fields/{f['field_id']}",
                     {"field_name": primary_name, "type": TEXT})
                print(f"    ~ primary → '{primary_name}'")
        else:
            lark("DELETE", f"/open-apis/bitable/v1/apps/{app}/tables/{tid}/fields/{f['field_id']}",
                 allow_fail=True)


def add_fields(app, ids, tid, specs):
    """specs: list of (name, type, property|None). Skips fields that already exist."""
    existing = {f["field_name"]: f["field_id"] for f in list_fields(app, tid)}
    for name, ftype, prop in specs:
        key = f"{tid}:{name}"
        if name in existing:
            ids["fields"][key] = existing[name]
            continue
        body = {"field_name": name, "type": ftype}
        if prop:
            body["property"] = prop
        data = lark("POST", f"/open-apis/bitable/v1/apps/{app}/tables/{tid}/fields", body)
        ids["fields"][key] = data["field"]["field_id"]
        save_ids(ids)
        print(f"    + {name}")


# ───────────────────────── schema definition (plain fields only) ─────────────────────────
def plain_fields(tables):
    """Return {table_name: [(name,type,prop),...]} for non-link / non-formula fields."""
    return {
        "Accounts": [
            ("Account ID", TEXT, None),
            ("Segment", SINGLE, sel("Enterprise", "Mid-Market", "SMB")),
            ("Industry", SINGLE, sel("Retail", "Tech", "Finance", "Manufacturing",
                                     "Healthcare", "Education", "Other")),
            ("Region", SINGLE, sel("North America", "EMEA", "APAC", "LATAM")),
            ("CSM Owner", SINGLE, sel(*CSMS)),
            ("Plan", SINGLE, sel(*PLANS)),
            ("Seats", NUMBER, None),
            ("Price per Seat (USD)", NUMBER, None),
            ("ARR (USD)", NUMBER, None),
            ("Status", SINGLE, sel("Onboarding", "Active", "At Risk", "Churned")),
            ("Start Date", DATE, None),
            ("Next Renewal Date", DATE, None),
            ("Renewal Forecast", SINGLE, sel("Renew", "Upsell", "Downsell", "Churn Risk", "Undecided")),
            ("Current Health Score", NUMBER, None),
            ("Avg Health 6mo", NUMBER, None),
            ("Last Snapshot", DATE, None),
            ("Notes", TEXT, None),
        ],
        "Usage Snapshots": [
            ("Month", DATE, None),
            ("Active Users", NUMBER, None),
            ("License Utilization %", NUMBER, None),
            ("Logins", NUMBER, None),
            ("Core Feature Adoption %", NUMBER, None),
            ("Advanced Feature Adoption %", NUMBER, None),
            ("Features Used", MULTI, sel("Dashboards", "Automations", "API", "Mobile",
                                         "Reports", "Integrations", "AI Assistant", "SSO")),
            ("Stickiness DAU-MAU %", NUMBER, None),
            ("Sentiment 0-10", NUMBER, None),
            ("Support Tickets", NUMBER, None),
        ],
        "Renewals": [
            ("Renewal Date", DATE, None),
            ("Current Plan", SINGLE, sel(*PLANS)),
            ("Current ARR (USD)", NUMBER, None),
            ("Proposed Plan", SINGLE, sel(*PLANS)),
            ("Proposed ARR (USD)", NUMBER, None),
            ("Forecast", SINGLE, sel("Pre-Renewal", "In Negotiation", "Won",
                                     "Upsell", "Downsell", "Churn")),
            ("Probability %", NUMBER, None),
            ("Outcome", SINGLE, sel("Pending", "Won", "Upsell", "Downsell", "Lost-Churn")),
            ("Owner", SINGLE, sel(*CSMS)),
            ("Notes", TEXT, None),
        ],
        "Revenue Movements": [
            ("Event Type", SINGLE, sel("New", "Renewal-Won", "Upsell", "Downsell",
                                       "Churn", "Reactivation")),
            ("Event Date", DATE, None),
            ("ARR Before (USD)", NUMBER, None),
            ("ARR After (USD)", NUMBER, None),
            ("Plan From", SINGLE, sel(*PLANS)),
            ("Plan To", SINGLE, sel(*PLANS)),
            ("Owner", SINGLE, sel(*CSMS)),
            ("Notes", TEXT, None),
        ],
        "Churn & Downsell Reasons": [
            ("Category", SINGLE, sel("Price", "Product Gap", "Adoption", "Competitor",
                                     "Budget", "Support", "Business Change", "Other")),
            ("Applies To", MULTI, sel("Churn", "Downsell")),
            ("Description", TEXT, None),
            ("Mitigation Playbook", TEXT, None),
        ],
        "CSM Activities": [
            ("Type", SINGLE, sel("QBR", "Check-in", "Onboarding", "Escalation",
                                 "Renewal Call", "Upsell Pitch")),
            ("Date", DATE, None),
            ("Owner", SINGLE, sel(*CSMS)),
            ("Status", SINGLE, sel("Planned", "Done", "Overdue")),
            ("Outcome / Next Steps", TEXT, None),
        ],
        "Commercial Targets": [
            ("CSM Owner", SINGLE, sel(*CSMS)),
            ("Quarter", SINGLE, sel(*QUARTERS)),
            ("Portfolio Accounts", NUMBER, None),
            ("Book of Business ARR (USD)", NUMBER, None),
            ("Renewal Target ARR (USD)", NUMBER, None),
            ("Renewal Actual ARR (USD)", NUMBER, None),
            ("Expansion Target ARR (USD)", NUMBER, None),
            ("Expansion Actual ARR (USD)", NUMBER, None),
            ("GRR Target %", NUMBER, None),
            ("GRR Actual %", NUMBER, None),
            ("NRR Target %", NUMBER, None),
            ("NRR Actual %", NUMBER, None),
        ],
    }


TABLE_PRIMARY = [
    ("Accounts", "Account Name"),
    ("Usage Snapshots", "Snapshot"),
    ("Renewals", "Renewal Name"),
    ("Revenue Movements", "Movement"),
    ("Churn & Downsell Reasons", "Reason"),
    ("CSM Activities", "Activity"),
    ("Commercial Targets", "Target Key"),
]

# (from_table, link_field, to_table, multiple, back_field_name)
LINKS = [
    ("Usage Snapshots", "Account", "Accounts", False, "Usage Snapshots"),
    ("Renewals", "Account", "Accounts", False, "Renewals"),
    ("Revenue Movements", "Account", "Accounts", False, "Revenue Movements"),
    ("CSM Activities", "Account", "Accounts", False, "Activities"),
    ("Revenue Movements", "Linked Renewal", "Renewals", False, "Revenue Movements"),
    ("CSM Activities", "Related Renewal", "Renewals", False, "Activities"),
    ("Renewals", "Reason", "Churn & Downsell Reasons", False, "Renewals"),
    ("Revenue Movements", "Reason", "Churn & Downsell Reasons", False, "Revenue Movements"),
]

# (table, field_name, formula_expression) — created last; ordered for intra-table deps
FORMULAS = [
    ("Usage Snapshots", "Health Score",
     "ROUND(0.3*{License Utilization %}+0.25*{Core Feature Adoption %}"
     "+0.15*{Advanced Feature Adoption %}+0.1*{Stickiness DAU-MAU %}"
     "+0.1*MIN({Sentiment 0-10}*10,100)+0.1*MAX(0,100-{Support Tickets}*10),0)"),
    ("Usage Snapshots", "Health Tier",
     'IF({Health Score}>=75,"🟢 Green",IF({Health Score}>=50,"🟡 Yellow","🔴 Red"))'),
    ("Renewals", "ARR Delta (USD)", "{Proposed ARR (USD)}-{Current ARR (USD)}"),
    ("Revenue Movements", "ARR Delta (USD)", "{ARR After (USD)}-{ARR Before (USD)}"),
    ("Commercial Targets", "Renewal Attainment %",
     "ROUND({Renewal Actual ARR (USD)}/{Renewal Target ARR (USD)}*100,0)"),
    ("Commercial Targets", "Expansion Attainment %",
     "ROUND({Expansion Actual ARR (USD)}/{Expansion Target ARR (USD)}*100,0)"),
    ("Commercial Targets", "NRR vs Target (pts)", "{NRR Actual %}-{NRR Target %}"),
    ("Commercial Targets", "Status",
     'IF({Renewal Actual ARR (USD)}/{Renewal Target ARR (USD)}>=1.05,"🟢 Ahead",'
     'IF({Renewal Actual ARR (USD)}/{Renewal Target ARR (USD)}>=0.95,"🟡 On Track","🔴 Behind"))'),
]


def add_links(app, ids):
    print("\n[Links]")
    for ftab, fname, totab, multiple, back in LINKS:
        ftid = ids["tables"][ftab]
        ttid = ids["tables"][totab]
        existing = {f["field_name"] for f in list_fields(app, ftid)}
        if fname in existing:
            continue
        prop = {"table_id": ttid, "multiple": multiple, "back_field_name": back}
        data = lark("POST", f"/open-apis/bitable/v1/apps/{app}/tables/{ftid}/fields",
                    {"field_name": fname, "type": BILINK, "property": prop})
        ids["fields"][f"{ftid}:{fname}"] = data["field"]["field_id"]
        save_ids(ids)
        print(f"    {ftab}.{fname} → {totab}  (back: {back})")


def add_formulas(app, ids):
    print("\n[Formulas]")
    for tab, fname, expr in FORMULAS:
        tid = ids["tables"][tab]
        existing = {f["field_name"] for f in list_fields(app, tid)}
        if fname in existing:
            continue
        data = lark("POST", f"/open-apis/bitable/v1/apps/{app}/tables/{tid}/fields",
                    {"field_name": fname, "type": FORMULA,
                     "property": {"formula_expression": expr}})
        ids["fields"][f"{tid}:{fname}"] = data["field"]["field_id"]
        save_ids(ids)
        print(f"    {tab}.{fname}")


def main():
    print("=== Customer Success Hub — schema builder ===")
    ids = load_ids()
    app = get_or_create_app(ids)

    specs = plain_fields(None)
    print("\n[Tables + plain fields]")
    for i, (tname, primary) in enumerate(TABLE_PRIMARY):
        if i == 0:
            tid = setup_first_table(app, ids, tname, primary)
        else:
            tid = get_or_create_table(app, ids, tname, primary)
        add_fields(app, ids, tid, specs[tname])

    add_links(app, ids)
    add_formulas(app, ids)

    print("\n" + "=" * 60)
    print(f"✅ Schema done. App token: {app}")
    print(f"   {ids.get('url')}")
    print(f"   ids saved → {IDS_PATH}")


if __name__ == "__main__":
    main()
