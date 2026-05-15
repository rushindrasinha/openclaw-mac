---
name: weekly-cost-report
description: Use when a user asks for a cost report, model usage summary, token spend breakdown, API costs, or says "how much did I spend this week?", "show me my API costs", "what's my model spend?", "weekly cost summary", or "usage report". Parses OpenClaw JSONL session logs and aggregates per-model token usage and dollar cost for the last 7 days.
---

# Weekly Cost Report

## Overview
Parses OpenClaw session JSONL logs to produce a per-model cost breakdown for the past 7 days. Reports total spend, per-model costs with percentages, and daily spend trend.

## Usage
```
python3 scripts/report.py
```

Output is printed to stdout. Pipe or forward to WhatsApp as needed.

## Workflow
1. Run `python3 scripts/report.py`
2. Script scans all `.jsonl` files in `~/.openclaw/agents/main/sessions/`
3. Filters to entries with timestamps in the last 7 days
4. Extracts `message.usage.cost.total` and `message.model` from each turn
5. Aggregates:
   - Total cost and turn count
   - Per-model cost and percentage of total
   - Per-day cost
6. Prints formatted WhatsApp-ready report

## Output Format
```
📊 Weekly API Cost Report
Period: last 7 days

Total: $X.XXXX across N,NNN turns

By model:
  anthropic/claude-sonnet-4-6: $X.XXXX (XX.X%)
  ...

By day:
  2026-03-17: $X.XXXX
  ...
```

## Scripts
- `scripts/report.py` — Standalone script. No arguments. Reads JSONL session logs, aggregates costs, prints report. Handles missing data gracefully (outputs "No API usage data found" if logs are empty or missing).

## Requirements
- Python 3.8+ (stdlib only — `json`, `os`, `glob`, `datetime`)
- OpenClaw session logs at `~/.openclaw/agents/main/sessions/*.jsonl`
