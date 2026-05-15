---
name: ai-agent-ops-briefing
description: Use when a user asks for a daily ops brief, morning briefing, customer status summary, MRR update, credit alerts, overdue payments, churn risk check, or outreach pipeline snapshot. Triggers on: "daily brief", "ops briefing", "how are my customers?", "MRR status", "who's overdue?", "credit alerts", "who's at risk of churning?", "morning update", "agent army status". Reads live data from ~/customers/ directory.
---

# AI Agent Ops Briefing

## Overview
Generates a WhatsApp-formatted morning ops briefing covering customer count, MRR, collected revenue, credit usage alerts, overdue payments, outreach pipeline status, and inactive customers (churn risk).

## Usage
```
python3 scripts/briefing.py
```

Output is printed to stdout. Pipe or forward to WhatsApp as needed.

Schedule via cron for 9 AM IST daily:
```
0 3 * * * /opt/homebrew/bin/python3 /path/to/skills-new/ai-agent-ops-briefing/scripts/briefing.py | openclaw message send --target <YOUR_E164_NUMBER> --channel whatsapp --message -
```

## Workflow
1. Run `python3 scripts/briefing.py`
2. Script reads live data from `~/customers/`:
   - Customer dirs (non-dot dirs) → active customer count
   - `~/customers/.payments/ledger.json` → MRR, total collected, paying customer count
   - Each customer's `usage.json` → credit usage %, grace zone status
   - `ledger.json` transactions → overdue payment detection (>35 days since last plan payment)
   - `~/customers/.outreach/tracker.json` → pipeline: total leads, unsent, closed
   - Each customer's `memory/*.md` filenames → last active date, days inactive
3. Assembles formatted report and prints to stdout

## Output Sections
- Active customer count
- MRR and total collected (INR)
- Credit alerts: 🔴 ≥90% used (upsell opp), 🟡 ≥75% used, ⚠️ in grace zone
- Overdue payments: customers with last plan payment >35 days ago
- Outreach pipeline: totals and today's send count
- Inactive customers: last active >3 days ago (churn risk)

## Scripts
- `scripts/briefing.py` — Standalone script. No arguments. Reads all data from `~/customers/` directory structure. Outputs WhatsApp-formatted multi-section briefing.

## Requirements
- Python 3.8+ (stdlib only — `json`, `os`, `datetime`, `pathlib`)
- `~/customers/` directory with standard customer directory structure
- `~/customers/.payments/ledger.json` for revenue data
- `~/customers/.outreach/tracker.json` for pipeline data (optional — section skipped if absent)
