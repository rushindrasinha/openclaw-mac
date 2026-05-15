#!/bin/zsh
# Fires when kill_switch.flag is created/modified
FLAG="$HOME/.openclaw/state/kill_switch.flag"
LOG="$HOME/.openclaw/logs/kill_switch.log"
mkdir -p "$(dirname $LOG)"
echo "[$(date)] Kill switch triggered" >> "$LOG"

# Optional WhatsApp notification — only fires if KILL_SWITCH_NOTIFY_TARGET is set
if [ -n "${KILL_SWITCH_NOTIFY_TARGET:-}" ] && command -v wacli &>/dev/null; then
  wacli send --to "$KILL_SWITCH_NOTIFY_TARGET" --message "🚨 AGENT KILL SWITCH TRIGGERED — all automation paused, outbound sends denied." 2>/dev/null
fi

# Disable all OpenClaw crons by pausing the gateway
openclaw gateway pause 2>/dev/null || true
echo "[$(date)] Gateway pause attempted" >> "$LOG"
