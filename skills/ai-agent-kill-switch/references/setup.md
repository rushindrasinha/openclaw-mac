# Kill Switch Setup

## How It Works
1. Watchdog monitors session logs for an ARMED trigger phrase
2. When detected: creates a sentinel file and pauses the gateway
3. Agent scripts check the sentinel before sending outbound messages
4. Clear the sentinel manually to resume

## LaunchAgent Setup (Persistent)
Create `~/Library/LaunchAgents/com.openclaw.killswitch.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.killswitch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>REPLACE_WITH_HOME/.openclaw/workspace/.agents/skills/ai-agent-kill-switch/scripts/kill_switch_watchdog.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/kill_switch_watchdog.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/kill_switch_watchdog.err</string>
</dict>
</plist>
```

> Replace `REPLACE_WITH_HOME` with the absolute path to your home directory (`echo $HOME`). LaunchAgent plists do not expand env vars.

Load: `launchctl load ~/Library/LaunchAgents/com.openclaw.killswitch.plist`

## Configure Trigger Phrase
The default armed phrase is `KILL: AGENT BANANA HAMMOCK NOW` (intentionally unusual so it isn't triggered by normal messages).

To change: edit `ARMED_PHRASE` at the top of `kill_switch_watchdog.sh`.

## Optional WhatsApp Notification
The trigger script (`kill_switch_trigger.sh`) will send a WhatsApp notification if you set:

```bash
export KILL_SWITCH_NOTIFY_TARGET="+1234567890"   # E.164 number or group JID
```

And have `wacli` installed.

## Integration in Agent Scripts
Source the flag-check helper at the top of any outbound-capable script:

```bash
source $HOME/.openclaw/workspace/.agents/skills/ai-agent-kill-switch/scripts/check_flag.sh
```

## Recovery
```bash
bash scripts/kill_switch.sh clear
```
