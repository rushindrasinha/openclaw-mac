#!/usr/bin/env python3
"""
Outreach Tracker for AaaS Agent Army
Tracks leads from initial contact through conversion.

Usage:
  python3 outreach_tracker.py add <name> <vertical> <phone_or_handle> [--source C1|C2|manual]
  python3 outreach_tracker.py import-csv <file.csv>  # Bulk import (name,vertical,contact,source)
  python3 outreach_tracker.py sent <lead_id>
  python3 outreach_tracker.py replied <lead_id> [--notes "interested"]
  python3 outreach_tracker.py booked <lead_id> [--date 2026-03-05]
  python3 outreach_tracker.py closed <lead_id> [--plan plus]
  python3 outreach_tracker.py dead <lead_id> [--reason "not interested"]
  python3 outreach_tracker.py pipeline            # Full pipeline view
  python3 outreach_tracker.py stats               # Conversion metrics
  python3 outreach_tracker.py today [--count 20]  # Today's outreach targets with messages
  python3 outreach_tracker.py message <lead_id>   # Generate personalized message for lead
"""

import json
import sys
import os
import csv
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
OUTREACH_DIR = Path(os.path.expanduser("~/customers/.outreach"))
TRACKER_PATH = OUTREACH_DIR / "tracker.json"
PITCH_DIR = Path(os.path.expanduser("~/customers/.pitch"))

STATUSES = ["new", "sent", "replied", "call_booked", "closed", "dead"]
VERTICALS = ["creator", "doctor", "business", "esports", "celebrity", "openclaw_user", "other"]

def load_tracker():
    if not TRACKER_PATH.exists():
        return {"leads": [], "next_id": 1, "daily_schedule": {}}
    with open(TRACKER_PATH) as f:
        return json.load(f)

def save_tracker(tracker):
    os.makedirs(OUTREACH_DIR, exist_ok=True)
    with open(TRACKER_PATH, 'w') as f:
        json.dump(tracker, f, indent=2)

def gen_lead_id(tracker):
    lid = f"L-{tracker['next_id']:04d}"
    tracker['next_id'] += 1
    return lid

def add_lead(name, vertical, contact, source="manual"):
    tracker = load_tracker()
    
    # Dedup by contact
    for l in tracker["leads"]:
        if l["contact"] == contact:
            print(f"  ⚠️  Duplicate: {contact} already exists as {l['id']} ({l['name']})")
            return None
    
    lid = gen_lead_id(tracker)
    now = datetime.now(IST)
    
    lead = {
        "id": lid,
        "name": name,
        "vertical": vertical if vertical in VERTICALS else "other",
        "contact": contact,
        "source": source,
        "status": "new",
        "created": now.isoformat(),
        "history": [{"action": "added", "date": now.isoformat()}],
        "notes": "",
        "plan": None,
        "call_date": None
    }
    
    tracker["leads"].append(lead)
    save_tracker(tracker)
    print(f"  ✅ {lid}: {name} ({vertical}) — {contact}")
    return lid

def update_status(lead_id, new_status, **kwargs):
    tracker = load_tracker()
    lead = next((l for l in tracker["leads"] if l["id"] == lead_id), None)
    if not lead:
        print(f"  ❌ Lead {lead_id} not found")
        return False
    
    now = datetime.now(IST)
    lead["status"] = new_status
    entry = {"action": new_status, "date": now.isoformat()}
    
    if "notes" in kwargs and kwargs["notes"]:
        lead["notes"] = kwargs["notes"]
        entry["notes"] = kwargs["notes"]
    if "plan" in kwargs and kwargs["plan"]:
        lead["plan"] = kwargs["plan"]
        entry["plan"] = kwargs["plan"]
    if "date" in kwargs and kwargs["date"]:
        lead["call_date"] = kwargs["date"]
        entry["call_date"] = kwargs["date"]
    if "reason" in kwargs and kwargs["reason"]:
        entry["reason"] = kwargs["reason"]
        lead["notes"] = kwargs["reason"]
    
    lead["history"].append(entry)
    save_tracker(tracker)
    
    status_icons = {"sent": "📤", "replied": "💬", "call_booked": "📞", "closed": "🎉", "dead": "💀"}
    icon = status_icons.get(new_status, "📌")
    print(f"  {icon} {lead_id} ({lead['name']}): → {new_status}")
    return True

def import_csv(filepath):
    """Import leads from CSV: name,vertical,contact,source"""
    tracker = load_tracker()
    existing_contacts = {l["contact"] for l in tracker["leads"]}
    
    added = 0
    skipped = 0
    
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        header = next(reader, None)  # Skip header
        for row in reader:
            if len(row) < 3:
                continue
            name = row[0].strip()
            vertical = row[1].strip() if len(row) > 1 else "other"
            contact = row[2].strip()
            source = row[3].strip() if len(row) > 3 else "manual"
            
            if contact in existing_contacts:
                skipped += 1
                continue
            
            lid = gen_lead_id(tracker)
            now = datetime.now(IST)
            tracker["leads"].append({
                "id": lid,
                "name": name,
                "vertical": vertical if vertical in VERTICALS else "other",
                "contact": contact,
                "source": source,
                "status": "new",
                "created": now.isoformat(),
                "history": [{"action": "added", "date": now.isoformat(), "source": f"import:{os.path.basename(filepath)}"}],
                "notes": "",
                "plan": None,
                "call_date": None
            })
            existing_contacts.add(contact)
            added += 1
    
    save_tracker(tracker)
    print(f"  ✅ Imported: {added} leads | Skipped (dupes): {skipped}")

def show_pipeline():
    tracker = load_tracker()
    leads = tracker["leads"]
    
    by_status = {}
    for l in leads:
        s = l["status"]
        by_status.setdefault(s, []).append(l)
    
    print("\n🪖 Agent Army — Outreach Pipeline")
    print("=" * 60)
    
    for status in STATUSES:
        group = by_status.get(status, [])
        icons = {"new": "🆕", "sent": "📤", "replied": "💬", "call_booked": "📞", "closed": "🎉", "dead": "💀"}
        print(f"\n{icons.get(status, '📌')} *{status.upper()}* ({len(group)})")
        for l in group[:20]:  # Cap display at 20 per status
            extra = ""
            if l.get("plan"):
                extra = f" | plan: {l['plan']}"
            if l.get("call_date"):
                extra += f" | call: {l['call_date']}"
            if l.get("notes"):
                extra += f" | {l['notes'][:40]}"
            print(f"  {l['id']}: {l['name']} ({l['vertical']}) — {l['contact']}{extra}")
        if len(group) > 20:
            print(f"  ... +{len(group)-20} more")
    
    print(f"\n{'=' * 60}")
    print(f"Total leads: {len(leads)}")

def show_stats():
    tracker = load_tracker()
    leads = tracker["leads"]
    total = len(leads)
    
    if total == 0:
        print("  No leads yet.")
        return
    
    counts = {}
    for l in leads:
        counts[l["status"]] = counts.get(l["status"], 0) + 1
    
    sent = counts.get("sent", 0) + counts.get("replied", 0) + counts.get("call_booked", 0) + counts.get("closed", 0) + counts.get("dead", 0)
    replied = counts.get("replied", 0) + counts.get("call_booked", 0) + counts.get("closed", 0)
    booked = counts.get("call_booked", 0) + counts.get("closed", 0)
    closed = counts.get("closed", 0)
    
    print("\n📊 Outreach Stats")
    print("=" * 40)
    print(f"  Total leads:    {total}")
    print(f"  New (unsent):   {counts.get('new', 0)}")
    print(f"  Sent:           {sent}")
    print(f"  Replied:        {replied}")
    print(f"  Calls booked:   {booked}")
    print(f"  Closed:         {closed}")
    print(f"  Dead:           {counts.get('dead', 0)}")
    print()
    if sent > 0:
        print(f"  Reply rate:     {replied/sent*100:.1f}%")
    if replied > 0:
        print(f"  Book rate:      {booked/replied*100:.1f}%")
    if booked > 0:
        print(f"  Close rate:     {closed/booked*100:.1f}%")
    if sent > 0:
        print(f"  Overall conv:   {closed/sent*100:.1f}%")
    
    # By vertical
    vert_counts = {}
    for l in leads:
        v = l["vertical"]
        vert_counts.setdefault(v, {"total": 0, "closed": 0})
        vert_counts[v]["total"] += 1
        if l["status"] == "closed":
            vert_counts[v]["closed"] += 1
    
    print("\n  By Vertical:")
    for v, c in sorted(vert_counts.items(), key=lambda x: -x[1]["total"]):
        print(f"    {v}: {c['total']} leads, {c['closed']} closed")

def get_today_targets(count=20):
    """Get today's outreach targets — prioritize by vertical then by creation order."""
    tracker = load_tracker()
    new_leads = [l for l in tracker["leads"] if l["status"] == "new"]
    
    # Priority: creators first (warmest), then openclaw_user, then rest
    priority = {"creator": 0, "openclaw_user": 1, "doctor": 2, "business": 3, "esports": 4, "celebrity": 5, "other": 6}
    new_leads.sort(key=lambda l: (priority.get(l["vertical"], 99), l["created"]))
    
    targets = new_leads[:count]
    
    if not targets:
        print("  ✅ No unsent leads remaining!")
        return
    
    print(f"\n📋 Today's Outreach ({len(targets)} leads)")
    print("=" * 60)
    for i, l in enumerate(targets, 1):
        print(f"\n  {i}. {l['id']}: *{l['name']}* ({l['vertical']})")
        print(f"     Contact: {l['contact']} | Source: {l['source']}")
        msg = generate_message(l)
        if msg:
            # Show first 2 lines of message
            lines = msg.strip().split('\n')
            preview = '\n'.join(lines[:2])
            print(f"     Message preview: {preview}...")
    
    print(f"\n  Run: outreach_tracker.py message <lead_id> for full message")

def generate_message(lead):
    """Generate personalized outreach message based on vertical."""
    vertical = lead["vertical"]
    name = lead["name"].split()[0] if lead["name"] else "there"
    
    # Map vertical to pitch file
    pitch_map = {
        "creator": "broadcast_creators.md",
        "openclaw_user": "broadcast_creators.md",  # Similar audience
        "doctor": "broadcast_doctors.md",
        "business": "broadcast_business.md",
        "esports": "broadcast_esports.md",
        "celebrity": "broadcast_celebrities.md",
        "other": "broadcast_business.md"
    }
    
    pitch_file = PITCH_DIR / pitch_map.get(vertical, "broadcast_business.md")
    if not pitch_file.exists():
        return None
    
    with open(pitch_file) as f:
        template = f.read()
    
    # Simple personalization: replace [Name] or {{name}} with actual name
    msg = template.replace("[Name]", name).replace("{{name}}", name).replace("{{NAME}}", name)
    return msg

def show_message(lead_id):
    tracker = load_tracker()
    lead = next((l for l in tracker["leads"] if l["id"] == lead_id), None)
    if not lead:
        print(f"  ❌ Lead {lead_id} not found")
        return
    
    print(f"\n📨 Message for: {lead['name']} ({lead['vertical']})")
    print(f"   Contact: {lead['contact']}")
    print("=" * 50)
    msg = generate_message(lead)
    if msg:
        print(msg)
    else:
        print("  ⚠️  No pitch template found for this vertical")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "add":
        if len(sys.argv) < 5:
            print("Usage: outreach_tracker.py add <name> <vertical> <contact> [--source C1|C2|manual]")
            sys.exit(1)
        source = "manual"
        for i, a in enumerate(sys.argv):
            if a == "--source" and i + 1 < len(sys.argv):
                source = sys.argv[i + 1]
        add_lead(sys.argv[2], sys.argv[3], sys.argv[4], source)
    
    elif cmd == "import-csv":
        if len(sys.argv) < 3:
            print("Usage: outreach_tracker.py import-csv <file.csv>")
            sys.exit(1)
        import_csv(sys.argv[2])
    
    elif cmd in ("sent", "replied", "call_booked", "booked", "closed", "dead"):
        if len(sys.argv) < 3:
            print(f"Usage: outreach_tracker.py {cmd} <lead_id> [--notes/--plan/--date/--reason ...]")
            sys.exit(1)
        actual_status = "call_booked" if cmd == "booked" else cmd
        kwargs = {}
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--notes" and i + 1 < len(sys.argv):
                kwargs["notes"] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == "--plan" and i + 1 < len(sys.argv):
                kwargs["plan"] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == "--date" and i + 1 < len(sys.argv):
                kwargs["date"] = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == "--reason" and i + 1 < len(sys.argv):
                kwargs["reason"] = sys.argv[i + 1]; i += 2
            else:
                i += 1
        update_status(sys.argv[2], actual_status, **kwargs)
    
    elif cmd == "pipeline":
        show_pipeline()
    
    elif cmd == "stats":
        show_stats()
    
    elif cmd == "today":
        count = 20
        for i, a in enumerate(sys.argv):
            if a == "--count" and i + 1 < len(sys.argv):
                count = int(sys.argv[i + 1])
        get_today_targets(count)
    
    elif cmd == "message":
        if len(sys.argv) < 3:
            print("Usage: outreach_tracker.py message <lead_id>")
            sys.exit(1)
        show_message(sys.argv[2])
    
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
