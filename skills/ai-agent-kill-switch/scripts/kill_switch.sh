#!/usr/bin/env bash
set -euo pipefail

# Agent kill switch: BANANA HAMMOCK
# Purpose: stop automation + prevent outbound sends.
# Safe to run multiple times.

STATE_DIR="${KILL_SWITCH_STATE_DIR:-$HOME/.openclaw/logs}"
mkdir -p "$STATE_DIR"
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$TS kill_switch invoked" >> "$STATE_DIR/kill-switch.log"

# 1) Hard-deny all outbound sends via config patch (requires gateway hot reload).
# We write a marker file; the agent will apply the patch.
cat > "$STATE_DIR/kill-switch.request.json" <<'JSON'
{
  "session": {
    "sendPolicy": {
      "default": "deny",
      "rules": [
        {"action":"deny","match":{"channel":"whatsapp","chatType":"group"}},
        {"action":"deny","match":{"channel":"whatsapp","chatType":"direct"}}
      ]
    }
  }
}
JSON

# 2) Pause the OpenClaw gateway (best effort)
if command -v openclaw >/dev/null 2>&1; then
  openclaw gateway pause 2>/dev/null || true
fi

echo "$TS kill_switch completed" >> "$STATE_DIR/kill-switch.log"
