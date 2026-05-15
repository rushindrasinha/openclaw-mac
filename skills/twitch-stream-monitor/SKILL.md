---
name: twitch-stream-monitor
description: Monitor Twitch channels going live, auto-record streams with streamlink, optionally upload recordings to Google Drive, and send WhatsApp notifications when streamers go online or finish.
---

## Overview

Polls Twitch channels every 5 minutes via cron. When a streamer goes live, starts recording automatically. When recording ends, uploads to Drive and sends a notification.

**Requirements:** `streamlink`, `ffprobe` (homebrew), `python3`. Drive upload requires a Google OAuth token (path configurable).

---

## Setup

### 1. Copy and configure channels.json

```bash
cd ~/.openclaw/workspace/.agents/skills/twitch-stream-monitor/scripts
cp channels.example.json channels.json
```

Edit `channels.json`:

```json
{
  "channels": [
    {"player": "DisplayName", "twitch": "twitchhandle"}
  ],
  "recordings_dir": "~/recordings/streams",
  "state_file": "/tmp/stream_monitor_state.json",
  "streamlink_path": "/opt/homebrew/bin/streamlink",
  "ffprobe_path": "/opt/homebrew/bin/ffprobe",
  "upload_script": "~/.openclaw/workspace/.agents/skills/twitch-stream-monitor/scripts/stream_upload.py",
  "notify_whatsapp_jid": "120363XXXXXXXXX@g.us",
  "notify_on_live": true,
  "notify_on_done": true
}
```

**Fields:**
- `channels` — list of `{player, twitch}` objects. `player` is display name; `twitch` is the Twitch handle.
- `recordings_dir` — where recordings are saved (created if missing)
- `state_file` — tracks active recording PIDs across cron runs
- `upload_script` — path to `stream_upload.py` (optional; omit to skip Drive upload)
- `notify_whatsapp_jid` — WhatsApp group JID to notify (optional; omit to print to stdout only)
- `notify_on_live` — send notification when stream starts
- `notify_on_done` — send notification with Drive link when stream ends

### 2. Install streamlink

```bash
brew install streamlink
```

### 3. Test manually

```bash
python3 ~/.openclaw/workspace/.agents/skills/twitch-stream-monitor/scripts/monitor.py
```

---

## Cron Setup

Run every 5 minutes:

```bash
crontab -e
```

Add:

```
*/5 * * * * /usr/bin/python3 $HOME/.openclaw/workspace/.agents/skills/twitch-stream-monitor/scripts/monitor.py >> /tmp/stream_monitor.log 2>&1
```

---

## How It Works

1. **Cron triggers monitor.py every 5 minutes**
2. **For each channel:**
   - If no active recording: check `streamlink --stream-url` for liveness
   - If live → spawn `streamlink` recording process → save PID to state file → notify "LIVE"
   - If already recording → check if PID is still alive
   - If PID died → stream ended → run upload script → notify with Drive link
3. **State persistence:** `/tmp/stream_monitor_state.json` tracks `{channel: {pid, file, started}}`

---

## Notifications

Notifications are sent via `openclaw message send --channel whatsapp`. Configure `notify_whatsapp_jid` with the target group or contact JID.

**Live notification:**
```
🔴 PlayerName is LIVE — Recording started
twitch.tv/handle
```

**Done notification:**
```
📁 PlayerName Stream — Recorded
🔗 https://drive.google.com/...
📹 1h 23m | 2400MB
```

---

## Drive Upload

Uses `stream_upload.py` (provided in this skill's `scripts/` folder). Requires:
- Google Drive API enabled
- OAuth token (path configured in the script — defaults to `~/.config/openclaw/google/token.json`)
- `pip3 install google-api-python-client google-auth`

Uploads to a configurable subfolder in the Drive root. Makes file public with view link.

---

## Troubleshooting

**streamlink not found:** Update `streamlink_path` in channels.json or install with `brew install streamlink`.

**Recording starts but stays empty:** Stream may require auth. Try `streamlink twitch.tv/CHANNEL best` manually.

**Cron not running:** Ensure full paths in crontab. Check `/tmp/stream_monitor.log`.

**State stuck (PID shows as alive but stream stopped):** Delete `/tmp/stream_monitor_state.json` and re-run.
