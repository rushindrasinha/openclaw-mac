#!/usr/bin/env python3
"""Weekly OpenClaw API cost report from session JSONL files."""
import json, os, glob
from datetime import datetime, timezone, timedelta

sessions_dir = os.path.expanduser(
    "~/.openclaw/agents/main/sessions"
)

costs = {}
daily = {}
total = 0
turns = 0
week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

for fpath in glob.glob(os.path.join(sessions_dir, "*.jsonl")):
    with open(fpath) as f:
        for line in f:
            try:
                obj = json.loads(line)
                ts = obj.get("timestamp", "")
                if ts < week_ago:
                    continue
                msg = obj.get("message", {})
                if not msg:
                    continue
                usage = msg.get("usage", {})
                if not usage:
                    continue
                cost_obj = usage.get("cost", {})
                t = cost_obj.get("total", 0)
                if not t:
                    continue
                model = msg.get("model", "unknown")
                costs[model] = costs.get(model, 0) + t
                day = ts[:10]
                daily[day] = daily.get(day, 0) + t
                total += t
                turns += 1
            except:
                pass

lines = ["📊 *Weekly API Cost Report*", f"_Period: last 7 days_", ""]
lines.append(f"*Total: ${total:.4f}* across {turns:,} turns")
lines.append("")
lines.append("*By model:*")
for m, c in sorted(costs.items(), key=lambda x: -x[1]):
    pct = c / total * 100 if total else 0
    lines.append(f"  {m}: ${c:.4f} ({pct:.1f}%)")
lines.append("")
lines.append("*By day:*")
for d, c in sorted(daily.items()):
    lines.append(f"  {d}: ${c:.4f}")

if not costs:
    lines = ["📊 *Weekly API Cost Report*", "No API usage data found for the past 7 days."]

print("\n".join(lines))
