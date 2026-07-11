# Customer Success Hub — a CSM operating system on Lark Base

**English** · [Tiếng Việt](README.vi.md)

A duplicate-able Lark Base template that turns the daily reality of a Customer Success
Manager into one connected system: **track your portfolio → measure health from real
feature usage → manage renewals → report churn / downsell / upsell revenue → and own a
commercial number.**

Built entirely with the Lark CLI (`@larksuite/cli`), so the whole thing is reproducible
from code — re-run two scripts and you get a fresh, fully-seeded copy.

> **All data is 100% fictional** (50 made-up companies, 5 made-up CSMs) — safe to publish.
> No real company, tenant, or personal data is used anywhere.

---

## 🎥 Demo video

https://github.com/nixthinh-bit/customer-success-hub/raw/main/assets/csmhub-demo.mp4

---

## (1) Duplicate this Base

> **▶️ [Duplicate this Base →](https://thinhle1.sg.larksuite.com/wiki/IS0AwYTdmiJIbxkOYsQlVwKbgLg?from=from_copylink)**
> Open the link and use **Save as / Make a copy** to get your own editable copy.

Two ways to get your own copy:

1. **Native (fastest):** open the demo Base → `···` menu → **Save as Template** / **Make a
   copy** → copy the share link and paste it above.
2. **From code (fresh + reproducible):**
   ```bash
   cd cs-hub
   python3 build_schema.py     # new Base + 7 tables + fields + links + formulas
   python3 seed_data.py        # fictional dataset (use --reset to reseed)
   python3 make_dashboard.py   # the two dashboards
   python3 workflows/setup_workflows.py   # the four automations (disabled)
   ```
   `build_schema.py` is idempotent and writes every id to `base_ids.json`.

---

## (2) What this Base is for

Most CSMs live across five disconnected places: a CRM for accounts, a spreadsheet for
health, another sheet for renewals, chat/email for churn notes, and a slide once a quarter
for "the number." That fragmentation causes five recurring pains — this Base is designed to
remove each one:

| CSM pain | How this Base fixes it |
|---|---|
| No single source of truth | One Base, **seven linked tables**, `Portfolio` as the hub |
| Health is a gut feeling | `Health Score` is **computed** from real usage signals, monthly |
| Renewals managed reactively | A renewal pipeline + a "4 weeks out" automation |
| Churn reasons aren't structured | A reference table of reasons, linked to every lost dollar |
| CS isn't tied to a number | A per-CSM **commercial scorecard** (GRR / NRR / attainment) |

**Use it to:** run your weekly portfolio review, spot at-risk accounts *before* they churn,
work renewals on a timeline, and report retention/expansion to leadership from live data.

---

## (3) Structure & how to enter data

`Portfolio` is the hub; every other table links back to it.

```
Portfolio (HUB) ── customer master: plan, ARR, status, renewal date, forecast, health
 ├─ Usage and Healthscore   monthly feature-usage → computed Health Score / Health Tier
 ├─ Renewals                renewal pipeline: date, plan, price, forecast, outcome
 ├─ Revenue Movements       every ARR event (New / Upsell / Downsell / Churn)
 ├─ CSM Activities          playbook: QBRs, check-ins, escalations, renewal calls
 └─ Commercial Targets      per-CSM × quarter quota: renewal / expansion / GRR / NRR
Churn & Downsell Reasons ── reference table → linked from Renewals & Revenue Movements
```

### The 7 tables — what to type, what is automatic

Legend: ⌨️ = you enter it · 🔗 = filled by linking a record · ⚙️ = computed (formula/rollup, **don't type**)

**Portfolio** — one row per customer (start here).
⌨️ Account Name, Segment, Industry, Region, CSM Owner, Plan, Seats, Price per Seat, Status,
Start Date, Next Renewal Date, Renewal Forecast · ⚙️ ARR (= Seats × Price), Current Health
Score, Avg Health 6mo, Last Snapshot · 🔗 Usage / Renewals / Revenue Movements / Activities.

**Usage and Healthscore** — one row per account **per month** (the engine of the model).
🔗 Account · ⌨️ Month, Active Users, License Utilization %, Logins, Core & Advanced Feature
Adoption %, Stickiness (DAU/MAU) %, Sentiment 0–10, Support Tickets · ⚙️ **Health Score**,
**Health Tier**.

**Renewals** — one row per renewal event.
🔗 Account, Reason (if lost/contracted) · ⌨️ Renewal Date, Current/Proposed Plan,
Current/Proposed ARR, Forecast, Probability %, Outcome, Owner · ⚙️ ARR Delta.

**Revenue Movements** — one row per ARR change (the revenue source of truth).
🔗 Account, Linked Renewal, Reason · ⌨️ Event Type, Event Date, ARR Before, ARR After,
Plan From/To, Owner · ⚙️ ARR Delta.

**Churn & Downsell Reasons** — reference list (fill once, reuse everywhere).
⌨️ Reason, Category, Applies To, Description, Mitigation Playbook.

**CSM Activities** — your playbook log.
🔗 Account, Related Renewal · ⌨️ Type, Date, Owner, Status, Outcome / Next Steps.

**Commercial Targets** — per-CSM per-quarter scorecard.
⌨️ CSM Owner, Quarter, Book of Business ARR, Renewal & Expansion Target/Actual, GRR & NRR
Target/Actual · ⚙️ Renewal & Expansion Attainment %, NRR vs Target, Status.

### The Health Score — computed, not guessed

`Health Score` (0–100) is a weighted formula over real usage signals:

```
0.30 · License Utilization %      + 0.25 · Core Feature Adoption %
0.15 · Advanced Feature Adoption % + 0.10 · Stickiness (DAU/MAU)
0.10 · Sentiment (→0-100)         + 0.10 · (100 − Support Tickets·10)
```

`Health Tier` buckets it 🟢 ≥75 / 🟡 50–74 / 🔴 <50. Because it's monthly, you see **trends** —
at-risk accounts visibly decline before they churn.

### Trim it to what you need

You don't have to keep all seven tables. Suggested tiers:

- **Lean start (5 tables):** `Portfolio`, `Usage and Healthscore`, `Renewals`,
  `Revenue Movements`, `Churn & Downsell Reasons`. This covers health + renewals + churn
  reporting — enough for most CSMs.
- **Add when ready:** `CSM Activities` (only if you want to log QBRs/check-ins in the Base
  rather than a calendar), and `Commercial Targets` (only if CS carries a quota — it's the
  most advanced piece; skip it and nothing else breaks).
- **Field-level trims:** `Notes`, `Avg Health 6mo`, `Last Snapshot`, `Probability %` are all
  optional. Delete the fields you won't maintain rather than leaving them half-filled.

To remove a table/field: do it in the Base UI, or delete it from `build_schema.py` before
duplicating so fresh copies never include it.

---

## (4) Workflows — set up & maintain

Four automations ship as JSON recipes plus a one-command installer. They are created
**disabled**, so you review the recipient and conditions before anything fires.

```bash
python3 workflows/setup_workflows.py            # create all four (disabled)
python3 workflows/setup_workflows.py --enable   # create AND turn them on
python3 workflows/setup_workflows.py --dry-run  # validate only, create nothing
```

The installer resolves **your** Lark `open_id` and routes alerts to you by default.

| # | Flow | Fires when |
|---|------|-----------|
| ① | **Health → Red alert** | a usage snapshot shows `Health Score < 50` |
| ② | **Renewal approaching** | ~4 weeks before a `Renewal Date` that's still `Pending` |
| ③ | **Churn / Downsell logged** | a Revenue Movement is `Churn` or `Downsell` |
| ④ | **Activity due** | 1 day before a `Planned` CSM Activity's `Date` |

**Editing flows** (thresholds, timing, message text, routing to the real CSM via a Person
field, or a true D-60 renewal sweep) is documented in
**[workflows/README.md](workflows/README.md)** — both the UI way and the versioned-in-code
way. Existing flows are listed with `lark-cli base +workflow-list` and updated with
`+workflow-update`.

### Dashboards (already built, charts-as-code)
`make_dashboard.py` builds two dashboards matched to two reporting cadences:
- **CSM Weekly Review** (operational, grouped by CSM): accounts, avg health, book ARR by
  CSM, status/health by CSM, renewal pipeline, activities.
- **Executive Monthly — BOD** (strategic): total ARR, blended NRR%/GRR%, ARR bridge by event
  type, ARR by segment/industry, churn ARR by reason, renewal funnel, NRR% by CSM.

---

## Files

| File | Role |
|---|---|
| `build_schema.py` | Creates the Base, tables, fields, links, formulas |
| `gen_data.py` | Deterministic fictional-data generator (`random.seed(42)`) |
| `seed_data.py` | Batch-creates records, resolving link fields to record ids |
| `make_dashboard.py` | Builds the two reporting dashboards (charts-as-code) |
| `workflows/` | Four automation recipes + `setup_workflows.py` installer |
| `base_ids.example.json` | Shape of the build output; the real `base_ids.json` (your app_token + Base URL) is generated locally and git-ignored |

## Notes
- Currency is **USD** throughout. `CSM Owner` is a Select (not a Person field) so the
  fictional dataset is self-contained — see workflows/README.md to switch to real people.
- The CLI token used here has Bitable **write** scope but not record **read** scope — it
  doesn't affect using the Base; counts are just verified in the Base UI.
