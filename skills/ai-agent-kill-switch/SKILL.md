---
name: ai-agent-kill-switch
description: Phrase-triggered emergency stop system for AI agents. Instantly halts all agent automation when a trigger phrase is detected. Use when setting up a safety kill switch, emergency stop, or pause-all-automation mechanism for autonomous agents. Triggers on: "kill switch", "emergency stop", "pause all automation", "safety stop", "agent kill switch". Genuinely novel — uses LaunchAgent watchdog for persistence across restarts.
---

# AI Agent Kill Switch

## Overview
Hard stop for autonomous agents. Trigger phrase → flag file → all outbound halts. Survives restarts via LaunchAgent.

## Quick Setup
1. Install watchdog as LaunchAgent (see references/setup.md)
2. Configure trigger phrase (default: "STOP ALL AGENTS")
3. Add check_flag.sh source to any agent script

## Activate / Clear
bash scripts/kill_switch.sh activate   # manual activate
bash scripts/kill_switch.sh clear       # resume automation
bash scripts/kill_switch.sh status      # check state

## Integration
Source check_flag.sh in any script before outbound actions:
  source scripts/check_flag.sh  # exits 99 if kill switch active

## Full Setup
See references/setup.md for LaunchAgent plist, phrase config, and recovery steps.
