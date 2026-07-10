# Automations (workflows)

**English** · [Tiếng Việt](README.vi.md)

Four ready-to-run automations for the Customer Success Hub, shipped as JSON recipes
plus a one-command installer. They are created **disabled** so you review and set the
recipient before anything fires.

## Install

```bash
# from the repo root
python3 workflows/setup_workflows.py            # create all four (disabled)
python3 workflows/setup_workflows.py --enable   # create AND turn them on
python3 workflows/setup_workflows.py --dry-run  # validate only — creates nothing
```

The installer reads the Base token from `../base_ids.json`, resolves **your** Lark
`open_id` automatically (so alerts land in your own Lark), injects a unique
`client_token` per workflow, and calls `lark-cli base +workflow-create`.
Send alerts to someone/somewhere else with `--receiver ou_xxxxx`.

## The four flows

| # | File | Trigger | What fires | Message goes to |
|---|------|---------|------------|-----------------|
| ① | `01-health-red-alert.json` | A **Usage & Healthscore** row where `Health Score < 50` is added/edited | "Account health dropped to Red" | you (base owner) |
| ② | `02-renewal-approaching.json` | **4 weeks before** a `Renewal Date`, if `Outcome = Pending` | "Renewal approaching" | you |
| ③ | `03-churn-downsell-logged.json` | A **Revenue Movement** with `Event Type = Churn or Downsell` | "Churn/Downsell logged — attach a reason" | you |
| ④ | `04-activity-due.json` | **1 day before** a `CSM Activity` `Date`, if `Status = Planned` | "Activity due tomorrow" | you |

> **Why "you" and not the account's CSM?** `CSM Owner` in this template is a *Select*
> field with fictional names, which a message step can't address. See "Route to the real
> CSM" below to switch to real DMs.

## How each recipe is built

Every file is a full workflow body: `{ client_token, title, steps[] }`.
A step is `{ id, type, title, next, data }`; `next` chains steps, `null` ends the flow.

- **Triggers** — `ChangeRecordTrigger` (row added/edited, filtered by `condition_list`),
  `ReminderTrigger` (N days/weeks before a date field), `TimerTrigger` (schedule).
- **Action** — `LarkMessageAction` with `receiver`, `title`, `content[]`, `btn_list[]`.
- **Refs** — message text pulls live values with `{ "value_type": "ref", "value": "$.t1.<fieldId>" }`.
  `$.t1.recordLink` is the record's URL (used by the "Open record" button).

`condition_list` is an OR-array of AND-groups:

```json
"condition_list": [
  { "conjunction": "and", "conditions": [
    { "field_name": "Health Score", "operator": "isLess", "value": [{ "value_type": "number", "value": 50 }] }
  ]}
]
```

Operators: `is` / `isNot` / `containsAny` / `doesNotContainAny` / `containsAll` /
`isEmpty` / `isNotEmpty` / `isGreater` / `isGreaterEqual` / `isLess` / `isLessEqual`.
For Select fields use `value_type: "option"` and `{ "name": "..." }`.

## How to edit a flow

**In the Base UI (easiest).** Open the Base → **Automations** → pick the flow → edit the
trigger condition, message text, or recipient → save. Good for tweaks.

**In code (versioned, repeatable).** Edit the JSON, then re-apply:

- Change a **threshold** → edit `condition_list[].conditions[].value` (e.g. `50` → `60`).
- Change **timing** → in `ReminderTrigger`, edit `unit` (`DAY`/`WEEK`/`MONTH`) + `offset`
  (DAY ∈ −7…7, WEEK ∈ 1…7). To notify at 60 days, see the Timer+Find recipe below.
- Change the **message** → edit the `content[]` array (mix `text` and `ref` items).
- Re-apply one file:
  ```bash
  lark-cli base +workflow-create --base-token <token> --json @workflows/01-health-red-alert.json
  ```
  (Set `client_token` to a fresh value first, or let `setup_workflows.py` do it.)
- **Update** an existing flow instead of creating a new one:
  `lark-cli base +workflow-list` → get its id → `+workflow-update --workflow-id <id> --json @file`.
- Enable / disable: `+workflow-enable` / `+workflow-disable --workflow-id <id>`.

### Route to the real CSM (optional)
1. In **Portfolio**, add a `CSM (person)` field of type **Person** and fill in the real CSMs.
2. In the recipe, change the action `receiver` from the fixed `open_id` to a ref that walks
   the link to that person, e.g. `{ "value_type": "ref", "value": "$.t1.<accountLinkFieldId>.<personFieldId>" }`.
3. Re-apply the file.

### Advanced: true "D-60" renewal sweep
`ReminderTrigger` maxes out around 7 weeks. For an exact 60-day window use a
`TimerTrigger` (daily) → `FindRecordAction` on **Renewals** filtered to
`Renewal Date` within 60 days and `Outcome = Pending` → `Loop` → `LarkMessageAction`.
Template this from the "定时+查找+循环" example in `lark-cli skills read lark-base
references/lark-base-workflow-guide.md`.
