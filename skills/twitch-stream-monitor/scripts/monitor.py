#!/usr/bin/env python3
"""
monitor.py — Generic Twitch stream monitor.
Checks all configured channels every run. If live and not already recording,
starts recording. When recording ends: optionally uploads to Drive + sends notification.
Run via cron every 5 minutes.

Config: channels.json (copy from channels.example.json)
"""

import subprocess, os, json, time, sys
from pathlib import Path
from datetime import datetime

# === LOAD CONFIG ===
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "channels.json"

if not CONFIG_FILE.exists():
    print(f"ERROR: {CONFIG_FILE} not found. Copy channels.example.json to channels.json and configure it.")
    sys.exit(1)

with open(CONFIG_FILE) as f:
    config = json.load(f)

CHANNELS        = config.get("channels", [])
RECORDINGS_DIR  = Path(os.path.expanduser(config.get("recordings_dir", "~/recordings/streams")))
STATE_FILE      = Path(os.path.expanduser(config.get("state_file", "/tmp/stream_monitor_state.json")))
STREAMLINK      = config.get("streamlink_path", "/opt/homebrew/bin/streamlink")
FFPROBE         = config.get("ffprobe_path", "/opt/homebrew/bin/ffprobe")
UPLOAD_SCRIPT   = config.get("upload_script")  # optional path to upload script
NOTIFY_JID      = config.get("notify_whatsapp_jid")  # optional WhatsApp group JID
NOTIFY_ON_LIVE  = config.get("notify_on_live", True)
NOTIFY_ON_DONE  = config.get("notify_on_done", True)

RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)


# === STATE ===
def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


# === CHECK IF LIVE ===
def is_live(channel):
    try:
        r = subprocess.run(
            [STREAMLINK, "--stream-url", f"twitch.tv/{channel}", "best"],
            capture_output=True, text=True, timeout=15
        )
        return r.returncode == 0 and "http" in r.stdout
    except Exception:
        return False


# === START RECORDING ===
def start_recording(player, channel):
    ts = int(time.time())
    date = datetime.now().strftime("%Y%m%d")
    filename = f"{channel}_{date}_{ts}.mp4"
    filepath = RECORDINGS_DIR / filename

    proc = subprocess.Popen(
        [STREAMLINK, "--twitch-low-latency", "--retry-streams", "5",
         "-o", str(filepath), f"twitch.tv/{channel}", "best"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print(f"▶ Started recording {player} ({channel}) → {filename} [PID {proc.pid}]")
    return proc.pid, str(filepath)


# === NOTIFY VIA OPENCLAW ===
def notify(message):
    if not NOTIFY_JID:
        print(f"[NOTIFY] {message}")
        return
    try:
        subprocess.run(
            ["openclaw", "message", "send",
             "--channel", "whatsapp",
             "--to", NOTIFY_JID,
             "--message", message],
            capture_output=True, timeout=30
        )
    except Exception as e:
        print(f"Notify failed: {e}")


# === UPLOAD TO DRIVE ===
def upload_to_drive(filepath, player, channel):
    if not UPLOAD_SCRIPT:
        return None
    date = datetime.now().strftime("%Y-%m-%d")
    display_name = f"{player}_{channel}_{date}.mp4"
    try:
        r = subprocess.run(
            ["python3", UPLOAD_SCRIPT, filepath, display_name],
            capture_output=True, text=True, timeout=3600
        )
        for line in r.stdout.splitlines():
            if "SHARE_LINK=" in line:
                return line.split("=", 1)[1].strip()
    except Exception as e:
        print(f"Upload failed: {e}")
    return None


# === GET RECORDING INFO ===
def get_recording_info(filepath):
    try:
        r = subprocess.run(
            [FFPROBE, "-v", "quiet", "-print_format", "json",
             "-show_format", filepath],
            capture_output=True, text=True, timeout=30
        )
        d = json.loads(r.stdout)["format"]
        dur = float(d["duration"])
        size_mb = int(d["size"]) // 1024 // 1024
        h, m = int(dur // 3600), int((dur % 3600) // 60)
        return f"{h}h {m}m", size_mb
    except Exception:
        return "?", "?"


# === MAIN ===
def main():
    if not CHANNELS:
        print("No channels configured. Edit channels.json.")
        sys.exit(1)

    state = load_state()

    for ch in CHANNELS:
        player  = ch.get("player", ch.get("twitch", "unknown"))
        channel = ch["twitch"]
        key     = channel

        current_pid  = state.get(key, {}).get("pid")
        current_file = state.get(key, {}).get("file")

        # Check if existing recording process is still alive
        if current_pid:
            try:
                os.kill(current_pid, 0)
                alive = True
            except ProcessLookupError:
                alive = False

            if not alive:
                # Stream ended — upload + notify
                print(f"✅ {player} stream ended. Processing...")
                duration, size_mb = get_recording_info(current_file)

                link = upload_to_drive(current_file, player, channel)

                if NOTIFY_ON_DONE:
                    if link:
                        notify(
                            f"📁 *{player} Stream — Recorded*\n\n"
                            f"🔗 {link}\n\n"
                            f"📹 {duration} | {size_mb}MB\n"
                            f"🔓 Anyone with link can view/download"
                        )
                    elif UPLOAD_SCRIPT:
                        notify(f"⚠️ {player} stream ended but Drive upload failed. File: {current_file}")
                    else:
                        notify(f"✅ {player} stream ended. File saved: {current_file} ({duration}, {size_mb}MB)")

                state.pop(key, None)
                save_state(state)
            else:
                print(f"⏺ {player} still recording [PID {current_pid}]")
            continue

        # Not currently recording — check if live
        live = is_live(channel)
        if live:
            pid, filepath = start_recording(player, channel)
            state[key] = {"pid": pid, "file": filepath, "started": int(time.time())}
            save_state(state)

            if NOTIFY_ON_LIVE:
                notify(
                    f"🔴 *{player} is LIVE — Recording started*\n"
                    f"twitch.tv/{channel}\n"
                    f"_(Link will follow when stream ends)_"
                )
        else:
            print(f"○ {player} ({channel}) — offline")

    print("Done.")


if __name__ == "__main__":
    main()
