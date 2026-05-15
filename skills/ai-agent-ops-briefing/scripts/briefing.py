#!/usr/bin/env python3
"""
Daily Ops Briefing — generates a WhatsApp-formatted morning briefing
for the Agent Army ops group. Run by cron at 9 AM IST daily.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
CUSTOMERS_DIR = Path(os.path.expanduser("~/customers"))
PAYMENTS_DIR = CUSTOMERS_DIR / ".payments"
OUTREACH_DIR = CUSTOMERS_DIR / ".outreach"

def load_json(path):
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)

def main():
    now = datetime.now(IST)
    lines = [
        f"🪖 *Agent Army — Daily Ops Briefing*",
        f"_{now.strftime('%A, %B %d, %Y')}_",
        f"━━━━━━━━━━━━━━━━━━━━━",
        ""
    ]

    # --- Customer count ---
    customer_dirs = [d for d in CUSTOMERS_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
    lines.append(f"👥 *Active Customers:* {len(customer_dirs)}")

    # --- Revenue from ledger ---
    ledger = load_json(PAYMENTS_DIR / "ledger.json")
    summary = ledger.get("summary", {})
    lines.append(f"💰 *MRR:* ₹{summary.get('mrr_inr', 0):,}")
    lines.append(f"💳 *Total Collected:* ₹{summary.get('total_collected_inr', 0):,}")
    lines.append(f"🏦 *Paying Customers:* {summary.get('total_customers_paid', 0)}")
    lines.append("")

    # --- Credit alerts ---
    alerts = []
    for d in customer_dirs:
        usage_file = d / "usage.json"
        if not usage_file.exists():
            continue
        usage = load_json(usage_file)
        total = usage.get("monthly_credits", 0) + usage.get("topup_balance", 0)
        used = usage.get("used", 0)
        if total > 0:
            pct = used / total * 100
            if pct >= 90:
                alerts.append(f"  🔴 {d.name}: {pct:.0f}% credits used — upsell opp")
            elif pct >= 75:
                alerts.append(f"  🟡 {d.name}: {pct:.0f}% credits used")
        grace = usage.get("grace_used", 0)
        if grace > 0:
            alerts.append(f"  ⚠️ {d.name}: in grace zone ({grace}/5)")

    if alerts:
        lines.append("*Credit Alerts:*")
        lines.extend(alerts)
        lines.append("")

    # --- Overdue payments ---
    txns = ledger.get("transactions", [])
    latest_plans = {}
    for t in txns:
        if t["type"] == "plan" and t["status"] == "confirmed" and t.get("plan") != "free" and t["amount_inr"] > 0:
            cid = t["customer_id"]
            if cid not in latest_plans or t["date"] > latest_plans[cid]["date"]:
                latest_plans[cid] = t
    overdue = []
    for cid, t in latest_plans.items():
        payment_date = datetime.strptime(t["date"], "%Y-%m-%d").replace(tzinfo=IST)
        if (now - payment_date).days > 35:
            overdue.append(f"  🔴 {cid}: {(now - payment_date).days - 30} days overdue")
    if overdue:
        lines.append("*Overdue Payments:*")
        lines.extend(overdue)
        lines.append("")

    # --- Outreach targets ---
    tracker = load_json(OUTREACH_DIR / "tracker.json")
    leads = tracker.get("leads", [])
    new_leads = [l for l in leads if l["status"] == "new"]
    total_leads = len(leads)
    closed = len([l for l in leads if l["status"] == "closed"])

    if total_leads > 0:
        lines.append(f"*Outreach Pipeline:*")
        lines.append(f"  📊 Total leads: {total_leads} | Unsent: {len(new_leads)} | Closed: {closed}")
        if new_leads:
            lines.append(f"  📋 Today's targets: {min(20, len(new_leads))} leads ready to send")
        lines.append("")

    # --- Inactive customers ---
    inactive = []
    for d in customer_dirs:
        memory_dir = d / "memory"
        if not memory_dir.exists():
            continue
        md_files = sorted(memory_dir.glob("*.md"), reverse=True)
        if md_files:
            latest = md_files[0].stem  # YYYY-MM-DD
            try:
                last_active = datetime.strptime(latest, "%Y-%m-%d").replace(tzinfo=IST)
                days = (now - last_active).days
                if days > 3:
                    inactive.append(f"  😴 {d.name}: {days} days since last activity")
            except ValueError:
                pass

    if inactive:
        lines.append("*Inactive (churn risk):*")
        lines.extend(inactive)
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append("_Run `outreach_tracker.py today` for personalized messages_")

    print("\n".join(lines))

if __name__ == "__main__":
    main()
