#!/usr/bin/env python3
"""
Seed the Customer Success Hub Base with the fictional dataset from gen_data.py.

Creates records table-by-table in dependency order, capturing record_ids so that
link fields (Account / Reason / Renewal) resolve to the right rows.

Usage:
  python3 seed_data.py            # seed (refuses if any table already has rows)
  python3 seed_data.py --reset    # delete all rows first, then seed fresh
"""
import os, sys, json
from build_schema import lark           # reuse the CLI helper + throttle
from gen_data import generate

HERE = os.path.dirname(os.path.abspath(__file__))
IDS_PATH = os.path.join(HERE, "base_ids.json")

ORDER = ["Churn & Downsell Reasons", "Accounts", "Renewals",
         "Usage Snapshots", "Revenue Movements", "CSM Activities", "Commercial Targets"]
PRIMARY = {"Accounts": "Account Name", "Churn & Downsell Reasons": "Reason",
           "Renewals": "Renewal Name", "Usage Snapshots": "Snapshot",
           "Revenue Movements": "Movement", "CSM Activities": "Activity",
           "Commercial Targets": "Target Key"}
LINK_TARGET = {"Account": "Accounts", "Reason": "Churn & Downsell Reasons",
               "Linked Renewal": "Renewals", "Related Renewal": "Renewals"}


def rec_path(app, tid, op):
    return f"/open-apis/bitable/v1/apps/{app}/tables/{tid}/records/{op}"


def list_record_ids(app, tid):
    """Returns [] if record-read scope is not granted (write-only token)."""
    ids, page = [], None
    while True:
        params = {"page_size": 500}
        if page:
            params["page_token"] = page
        data = lark("GET", f"/open-apis/bitable/v1/apps/{app}/tables/{tid}/records",
                    params=params, allow_fail=True)
        if not data:
            return ids
        ids += [r["record_id"] for r in data.get("items", [])]
        if not data.get("has_more"):
            break
        page = data.get("page_token")
    return ids


def clear_table(app, tid):
    ids = list_record_ids(app, tid)
    for i in range(0, len(ids), 500):
        lark("POST", rec_path(app, tid, "batch_delete"), {"records": ids[i:i+500]}, allow_fail=True)
    return len(ids)


def batch_create(app, tid, records):
    out = []
    for i in range(0, len(records), 100):
        data = lark("POST", rec_path(app, tid, "batch_create"),
                    {"records": [{"fields": f} for f in records[i:i+100]]})
        out += [r["record_id"] for r in data["records"]]
    return out


def main():
    reset = "--reset" in sys.argv
    with open(IDS_PATH) as f:
        ids = json.load(f)
    app = ids["app_token"]
    tables = ids["tables"]
    data = generate()

    if reset:
        print("[reset] clearing existing rows…")
        for t in reversed(ORDER):
            n = clear_table(app, tables[t])
            if n:
                print(f"  - {t}: deleted {n}")
    else:
        for t in ORDER:
            if list_record_ids(app, tables[t]):
                print(f"✗ '{t}' already has rows. Re-run with --reset to reseed.")
                sys.exit(1)

    maps = {}
    print("\n[seed]")
    for table in ORDER:
        recs = data[table]
        tid = tables[table]
        payload = []
        for r in recs:
            fields = {k: v for k, v in r.items() if not k.startswith("_")}
            for lf, names in r.get("_links", {}).items():
                tgt = LINK_TARGET[lf]
                rid_list = [maps[tgt][nm] for nm in names if nm in maps.get(tgt, {})]
                if rid_list:
                    fields[lf] = rid_list
            payload.append(fields)
        rids = batch_create(app, tid, payload)
        prim = PRIMARY[table]
        maps[table] = {recs[i][prim]: rids[i] for i in range(len(recs))}
        print(f"  ✓ {table:28s} {len(rids)} rows")

    print("\n✅ Seed complete →", ids.get("url"))


if __name__ == "__main__":
    main()
