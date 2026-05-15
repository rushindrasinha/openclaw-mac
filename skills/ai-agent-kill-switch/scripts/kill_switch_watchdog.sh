#!/usr/bin/env bash
set -euo pipefail

# Kill switch watchdog (Option 1 + 3)
# - Only triggers on ARMED phrase: "KILL: AGENT BANANA HAMMOCK NOW"
# - Incremental scan using state file (only new bytes)

ARMED_PHRASE="${KILL_SWITCH_PHRASE:-KILL: AGENT BANANA HAMMOCK NOW}"
STATE_DIR="${KILL_SWITCH_STATE_DIR:-$HOME/.openclaw/logs}"
SENTINEL="$STATE_DIR/kill-switch.triggered"
STATE_FILE="$STATE_DIR/kill-switch.watchdog.state.json"
SESS_DIR="$HOME/.openclaw/agents/main/sessions"

mkdir -p "$STATE_DIR"

# If already triggered, exit cleanly.
if [ -f "$SENTINEL" ]; then
  echo "TRIGGERED_ALREADY"
  exit 0
fi

# Load last processed mtime+size per file (simple incremental)
# Format: {"files": {"path": {"size":123}}}
export ARMED_PHRASE STATE_FILE SESS_DIR
python3 - <<'PY'
import json, os, glob
from pathlib import Path

armed = os.environ.get('ARMED_PHRASE','')
state_file = os.environ.get('STATE_FILE','')
sess_dir = Path(os.environ.get('SESS_DIR',''))
if state_file and os.path.exists(state_file):
    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
else:
    state = {"files": {}}
files_state = state.get('files', {})

triggered = False

# Scan only appended bytes since last recorded size.
for path in glob.glob(str(sess_dir / '*.jsonl')):
    try:
        p = Path(path)
        size = p.stat().st_size
    except FileNotFoundError:
        continue

    last_size = int(files_state.get(path, {}).get('size', 0) or 0)
    if last_size > size:
        # file rotated/truncated
        last_size = 0

    if size == last_size:
        continue

    with open(path, 'rb') as f:
        f.seek(last_size)
        chunk = f.read()

    try:
        text = chunk.decode('utf-8', errors='ignore')
    except Exception:
        text = ''

    if armed in text:
        triggered = True

    files_state[path] = {'size': size}

state['files'] = files_state
with open(state_file, 'w', encoding='utf-8') as f:
    json.dump(state, f)

print('TRIGGER' if triggered else 'NO_TRIGGER')
PY