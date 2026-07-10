#!/usr/bin/env python3
"""
Build the reporting dashboards (charts-as-code) on the CS Hub Base.

Two purpose-built dashboards:
  1. "CSM Weekly Review"      — operational, grouped by CSM (CSM → Head of CSM, weekly)
  2. "Executive Monthly — BOD"— strategic overview (Head of CSM → BOD, monthly)

Deletes the old generic "CS Commercial Overview" dashboard.

Charts use ONLY existing fields. data-config rules (verified):
  - series[].rollup ∈ {SUM, AVERAGE, MAX};  count_all:true to count rows
  - group_by must be a JSON ARRAY of {"field_name": ...}
Chart set = "standard & safe": statistics / column / bar / line / ring / pie / funnel.

Idempotent: reuses dashboards + skips blocks that already exist. Re-runnable.
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


RUN = _resolve_cli()

DELETE_DASHBOARDS = ["CS Commercial Overview"]


def base(*args, allow_fail=False):
    cmd = RUN + ["base"] + list(args) + ["--as", "user", "--format", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    raw = r.stdout if r.stdout.strip() else r.stderr
    i = raw.find("{")
    if i > 0:
        raw = raw[i:]
    try:
        resp = json.loads(raw)
    except Exception:
        if allow_fail:
            return None
        print("[PARSE ERR]", " ".join(args[:3]), "\n", r.stdout[:200], r.stderr[:200])
        sys.exit(1)
    if resp.get("ok") is False or resp.get("error"):
        if allow_fail:
            return resp  # caller inspects .error
        print("[ERR]", " ".join(args[:3]), "\n", json.dumps(resp.get("error", resp), ensure_ascii=False)[:300])
        sys.exit(1)
    time.sleep(0.12)
    return resp


def g(*fields):
    return [{"field_name": f} for f in fields]


def s(field, rollup):
    return [{"field_name": field, "rollup": rollup}]


DASHBOARDS = {
    # ── Dashboard 1: operational, grouped by CSM ──
    "CSM Weekly Review": [
        ("Total Accounts", "statistics", {"table_name": "Portfolio", "count_all": True}),
        ("Avg Current Health", "statistics",
         {"table_name": "Portfolio", "series": s("Current Health Score", "AVERAGE")}),
        ("Book ARR by CSM", "bar",
         {"table_name": "Portfolio", "group_by": g("CSM Owner"), "series": s("ARR (USD)", "SUM")}),
        ("Account Status by CSM", "column",
         {"table_name": "Portfolio", "group_by": g("CSM Owner", "Status"), "count_all": True}),
        ("Avg Health by CSM", "bar",
         {"table_name": "Portfolio", "group_by": g("CSM Owner"), "series": s("Current Health Score", "AVERAGE")}),
        ("ARR by Renewal Forecast", "column",
         {"table_name": "Portfolio", "group_by": g("Renewal Forecast"), "series": s("ARR (USD)", "SUM")}),
        ("Renewal pipeline by Owner & stage", "column",
         {"table_name": "Renewals", "group_by": g("Owner", "Forecast"), "series": s("Current ARR (USD)", "SUM")}),
        ("Activities by Owner & Status", "column",
         {"table_name": "CSM Activities", "group_by": g("Owner", "Status"), "count_all": True}),
    ],
    # ── Dashboard 2: strategic overview for BOD ──
    "Executive Monthly — BOD": [
        ("Total ARR (USD)", "statistics", {"table_name": "Portfolio", "series": s("ARR (USD)", "SUM")}),
        ("Blended NRR %", "statistics",
         {"table_name": "Commercial Targets", "series": s("NRR Actual %", "AVERAGE")}),
        ("Blended GRR %", "statistics",
         {"table_name": "Commercial Targets", "series": s("GRR Actual %", "AVERAGE")}),
        ("Total Logos", "statistics", {"table_name": "Portfolio", "count_all": True}),
        ("NRR % & GRR % by Quarter", "line",
         {"table_name": "Commercial Targets", "group_by": g("Quarter"),
          "series": [{"field_name": "NRR Actual %", "rollup": "AVERAGE"},
                     {"field_name": "GRR Actual %", "rollup": "AVERAGE"}]}),
        ("Net ARR by Event Type", "column",
         {"table_name": "Revenue Movements", "group_by": g("Event Type"), "series": s("ARR Delta (USD)", "SUM")}),
        ("ARR by Segment", "ring",
         {"table_name": "Portfolio", "group_by": g("Segment"), "series": s("ARR (USD)", "SUM")}),
        ("ARR by Industry", "bar",
         {"table_name": "Portfolio", "group_by": g("Industry"), "series": s("ARR (USD)", "SUM")}),
        ("Churn-Downsell ARR by Reason", "bar",
         {"table_name": "Revenue Movements", "group_by": g("Reason"), "series": s("ARR Delta (USD)", "SUM")}),
        ("Renewal pipeline ARR by Forecast", "funnel",
         {"table_name": "Renewals", "group_by": g("Forecast"), "series": s("Current ARR (USD)", "SUM")}),
        ("NRR % by CSM", "bar",
         {"table_name": "Commercial Targets", "group_by": g("CSM Owner"), "series": s("NRR Actual %", "AVERAGE")}),
    ],
}


def list_dashboards(app):
    d = base("+dashboard-list", "--base-token", app, allow_fail=True)
    if not d or d.get("error"):
        return []
    data = d.get("data", {})
    return data.get("dashboards", data.get("items", []))


def block_names(app, dash_id):
    d = base("+dashboard-block-list", "--base-token", app, "--dashboard-id", dash_id, allow_fail=True)
    if not d or d.get("error"):
        return set()
    data = d.get("data", {})
    items = data.get("blocks", data.get("items", []))
    return {b.get("name") for b in items if b.get("name")}


def main():
    with open(IDS_PATH) as f:
        ids = json.load(f)
    app = ids["app_token"]
    ids.setdefault("dashboards", {})

    existing = {d.get("name"): (d.get("dashboard_id") or d.get("block_id")) for d in list_dashboards(app)}

    # 1) delete the old generic dashboard
    for name in DELETE_DASHBOARDS:
        did = ids["dashboards"].pop(name, None) or existing.get(name)
        if did:
            base("+dashboard-delete", "--base-token", app, "--dashboard-id", did, "--yes", allow_fail=True)
            print(f"🗑  deleted old dashboard '{name}' ({did})")
        ids["dashboards"].pop("_blocks", None)

    # 2) build the two dashboards
    for dname, blocks in DASHBOARDS.items():
        dash_id = ids["dashboards"].get(dname) or existing.get(dname)
        if not dash_id:
            data = base("+dashboard-create", "--base-token", app, "--name", dname)
            dash_id = data["data"]["dashboard"]["dashboard_id"]
            print(f"\n✓ created dashboard '{dname}' ({dash_id})")
        else:
            print(f"\n• reusing dashboard '{dname}' ({dash_id})")
        ids["dashboards"][dname] = dash_id

        have = block_names(app, dash_id)
        for name, btype, cfg in blocks:
            if name in have:
                print(f"  • {btype:11s} {name}  (exists)")
                continue
            resp = base("+dashboard-block-create", "--base-token", app, "--dashboard-id", dash_id,
                        "--name", name, "--type", btype,
                        "--data-config", json.dumps(cfg, ensure_ascii=False), allow_fail=True)
            if resp and resp.get("ok") is not False and not resp.get("error"):
                print(f"  ✓ {btype:11s} {name}")
            else:
                err = (resp or {}).get("error", {})
                print(f"  ✗ {btype:11s} {name}  → {err.get('message', 'failed')}")

        base("+dashboard-arrange", "--base-token", app, "--dashboard-id", dash_id, allow_fail=True)

    with open(IDS_PATH, "w") as f:
        json.dump(ids, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Done → {ids.get('url')}")


if __name__ == "__main__":
    main()
