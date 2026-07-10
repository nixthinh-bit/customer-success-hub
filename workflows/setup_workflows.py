#!/usr/bin/env python3
"""
Create the Customer Success Hub automations in your Base — one command.

    python3 workflows/setup_workflows.py            # create all (disabled)
    python3 workflows/setup_workflows.py --enable   # create AND turn them on
    python3 workflows/setup_workflows.py --dry-run   # print requests, create nothing
    python3 workflows/setup_workflows.py --receiver ou_xxx   # send alerts to a specific person

What it does
------------
* Reads the Base app_token from ../base_ids.json.
* Resolves *your* Lark open_id (via `lark-cli config show`) and drops it into every
  workflow's message receiver — so alerts land in your own Lark by default.
* Loads every workflows/NN-*.json recipe, injects a unique client_token, and calls
  `lark-cli base +workflow-create`.
* New workflows are created **disabled**. Pass --enable to switch them on, or flip
  them yourself in the Base UI (Automations panel).

No personal ids are stored in this repo — the open_id is fetched at runtime.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_IDS = HERE.parent / "base_ids.json"


def lark_cmd():
    """Return the argv prefix that runs the Lark CLI on this machine."""
    for probe in (["lark-cli"], ["lark"], ["npx", "--no-install", "@larksuite/cli"]):
        try:
            r = subprocess.run(probe + ["--version"], capture_output=True, text=True)
            if r.returncode == 0:
                return probe
        except FileNotFoundError:
            continue
    sys.exit("Could not find the Lark CLI. Install it: npm i -g @larksuite/cli")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def resolve_receiver(cli):
    """Pull the current user's open_id (ou_...) from the CLI config."""
    r = run(cli + ["config", "show"])
    m = re.search(r"ou_[0-9a-f]+", r.stdout or "")
    if m:
        return m.group(0)
    sys.exit("Could not resolve your open_id from `lark-cli config show`. "
             "Pass one explicitly with --receiver ou_xxx.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--enable", action="store_true", help="enable each workflow after creating it")
    ap.add_argument("--dry-run", action="store_true", help="print the request, create nothing")
    ap.add_argument("--receiver", help="open_id (ou_...) to receive alerts; defaults to you")
    args = ap.parse_args()

    cli = lark_cmd()
    app_token = json.loads(BASE_IDS.read_text())["app_token"]
    receiver = args.receiver or resolve_receiver(cli)
    print(f"Base   : {app_token}")
    print(f"Alerts → : {receiver}\n")

    recipes = sorted(HERE.glob("[0-9]*.json"))
    if not recipes:
        sys.exit("No workflow recipes found next to this script.")

    for path in recipes:
        body = path.read_text()
        body = body.replace("__RECEIVER_OPEN_ID__", receiver)
        body = body.replace("__CLIENT_TOKEN__", f"csh-{path.stem}-{int(time.time()*1000)}")
        title = json.loads(body)["title"]

        # The CLI's @file only accepts a relative path inside the cwd, so drop the
        # temp file in the current directory and pass just its basename.
        tmp = Path.cwd() / f".cshwf_{path.stem}.tmp.json"
        tmp.write_text(body)
        cmd = cli + ["base", "+workflow-create", "--base-token", app_token, "--json", f"@{tmp.name}"]
        if args.dry_run:
            cmd.append("--dry-run")

        print(f"→ {title}")
        r = run(cmd)
        tmp.unlink(missing_ok=True)
        if args.dry_run:
            ok = "=== Dry Run ===" in (r.stdout or "") or '"url"' in (r.stdout or "")
            print("  ✓ request built (dry-run, nothing created)" if ok
                  else f"  ! dry-run problem:\n{r.stdout or r.stderr}")
            continue
        try:
            out = json.loads(r.stdout)
        except (json.JSONDecodeError, TypeError):
            print(f"  ! CLI returned non-JSON:\n{r.stdout or r.stderr}")
            continue
        if not out.get("ok"):
            print(f"  ! failed: {json.dumps(out.get('error'), ensure_ascii=False)}")
            continue

        wf_id = (out.get("data") or {}).get("workflow_id") or (out.get("data") or {}).get("id")
        print(f"  ✓ created (disabled): {wf_id}")

        if args.enable and wf_id and not args.dry_run:
            e = run(cli + ["base", "+workflow-enable", "--base-token", app_token, "--workflow-id", wf_id])
            ok = "✓ enabled" if '"ok": true' in (e.stdout or "") else "! enable failed"
            print(f"  {ok}")

    print("\nDone. Open the Base → Automations to review, edit receivers, or toggle them.")


if __name__ == "__main__":
    main()
