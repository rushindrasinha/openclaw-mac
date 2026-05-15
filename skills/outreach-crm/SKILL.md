---
name: outreach-crm
description: Use when a user wants to track sales leads or outreach, add new prospects, update lead status (sent/replied/booked/closed/dead), view the full pipeline, check conversion stats, get today's outreach targets, or generate personalized messages for leads. Triggers on: "add this lead", "mark as replied", "show pipeline", "outreach stats", "who should I message today", "track this prospect", "update lead status", "close this deal", "CRM". JSON-backed, no database required.
---

# Outreach CRM

## Overview
Lightweight JSON-backed lead tracker for the Agent Army outreach pipeline. Tracks leads from new → sent → replied → booked → closed (or dead), with vertical-based prioritization and personalized message generation.

## Usage

```
python3 scripts/outreach.py add <name> <vertical> <contact> [--source C1|C2|manual]
python3 scripts/outreach.py sent <lead_id>
python3 scripts/outreach.py replied <lead_id> [--notes "interested"]
python3 scripts/outreach.py booked <lead_id> [--date 2026-03-05]
python3 scripts/outreach.py closed <lead_id> [--plan plus]
python3 scripts/outreach.py dead <lead_id> [--reason "not interested"]
python3 scripts/outreach.py pipeline
python3 scripts/outreach.py stats
python3 scripts/outreach.py today [--count 20]
python3 scripts/outreach.py message <lead_id>
python3 scripts/outreach.py import-csv <file.csv>
```

Verticals: `creator`, `doctor`, `business`, `esports`, `celebrity`, `openclaw_user`, `other`

## Workflow

**Adding a lead:**
1. Run `add <name> <vertical> <contact>` — deduplicates by contact, assigns L-XXXX ID
2. Lead is stored with status `new` in `~/customers/.outreach/tracker.json`

**Moving through pipeline:**
1. Use status commands (`sent`, `replied`, `booked`, `closed`, `dead`) with the lead ID
2. Each update appends to the lead's history log with timestamp

**Viewing pipeline:**
1. `pipeline` — full view grouped by status, capped at 20 per bucket
2. `stats` — conversion rates: reply rate, book rate, close rate, by vertical
3. `today` — prioritized list of unsent leads (creators first, then openclaw_user, doctor, business, esports, celebrity, other)

**Generating outreach messages:**
1. `message <lead_id>` — loads pitch template from `~/customers/.pitch/broadcast_<vertical>.md`
2. Replaces `[Name]` / `{{name}}` with lead's first name

## Scripts
- `scripts/outreach.py` — Full CRM logic: `add_lead`, `update_status`, `show_pipeline`, `show_stats`, `get_today_targets`, `generate_message`, `import_csv`. Data stored at `~/customers/.outreach/tracker.json`. Pitch templates at `~/customers/.pitch/`.

## Requirements
- Python 3.8+ (stdlib only — `json`, `csv`, `datetime`, `pathlib`)
- `~/customers/.outreach/` directory (auto-created on first add)
- Optional: pitch template files at `~/customers/.pitch/broadcast_<vertical>.md` for message generation
