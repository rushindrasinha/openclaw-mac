#!/usr/bin/env python3
"""
suno-music-gen — AI music generation via Suno's browser API.

⚠️  WARNING: This uses Suno's internal/undocumented API extracted from browser sessions.
    - For personal use only.
    - Check Suno's Terms of Service before using: https://suno.com/tos
    - Token expires; re-run --set-token when auth fails.

Setup:
  1. Open https://suno.com/create in Chrome and log in
  2. Open DevTools → Network tab
  3. Trigger any generation (or wait for a request to studio-api.prod.suno.com)
  4. Click the request → Headers → copy "Authorization" value (starts with "Bearer ")
  5. Run: python3 generate.py --set-token "Bearer <your_token>"

Usage:
  python3 generate.py --set-token "Bearer <token>"   # save token
  python3 generate.py --check                         # verify auth + show credits
  python3 generate.py --prompt "chill lo-fi beats"    # generate with vocals
  python3 generate.py --prompt "epic battle music" --instrumental
  python3 generate.py --prompt "..." --out ~/my_track.mp3
  python3 generate.py --prompt "..." --custom --tags "hip-hop" --title "My Song"
"""

import os
import json
import time
import base64
import argparse
import requests
from pathlib import Path

# Token stored at ~/.suno_token (public/portable location, not openclaw-specific)
TOKEN_FILE = Path.home() / ".suno_token"
DEVICE_ID  = "fc127c2e-800e-49b8-8fa3-1d93f35ab345"
SUNO_BASE  = "https://studio-api.prod.suno.com"
UA         = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36"


# ─── Auth ────────────────────────────────────────────────────────────────────

def _read_token() -> str:
    token = os.environ.get("SUNO_BEARER_TOKEN", "").strip()
    if not token and TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text().strip()
    if not token:
        raise ValueError(
            "No token found.\n"
            "Run: python3 generate.py --set-token \"Bearer <token>\"\n"
            "Get token: DevTools → Network → any studio-api.prod.suno.com request → Authorization header"
        )
    if not token.startswith("Bearer "):
        raise ValueError(
            f"Token must start with 'Bearer '. Got: {token[:30]}...\n"
            "Copy the full Authorization header value from DevTools."
        )
    return token


def set_token(token: str):
    token = token.strip()
    if not token.startswith("Bearer "):
        print("WARNING: Token doesn't start with 'Bearer '. Make sure you copied the full Authorization header.")
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)
    print(f"Token saved to {TOKEN_FILE}")
    check()


def _browser_token() -> str:
    ts_ms = int(time.time() * 1000)
    inner = base64.b64encode(json.dumps({"timestamp": ts_ms}).encode()).decode().rstrip("=")
    return json.dumps({"token": inner})


def _headers(content_type: bool = False) -> dict:
    token = _read_token()
    h = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://suno.com",
        "Referer": "https://suno.com/",
        "Affiliate-Id": "undefined",
        "Device-Id": DEVICE_ID,
        "Browser-Token": _browser_token(),
        "Authorization": token,
    }
    if content_type:
        h["Content-Type"] = "application/json"
    return h


# ─── Check ───────────────────────────────────────────────────────────────────

def check():
    try:
        r = requests.get(f"{SUNO_BASE}/api/billing/info/", headers=_headers(), timeout=30)
        if r.status_code == 401:
            print("Auth failed (401). Token may be expired. Re-run --set-token.")
            return False
        info = r.json()
        plan = info.get("plan", {}).get("name", "unknown")
        credits = info.get("total_credits_left", "?")
        print(f"Connected to Suno | Plan: {plan} | Credits remaining: {credits}")
        return True
    except Exception as e:
        print(f"Check failed: {e}")
        return False


# ─── Generate ────────────────────────────────────────────────────────────────

def generate(
    prompt: str,
    instrumental: bool = False,
    model: str = "chirp-crow",
    custom: bool = False,
    tags: str = "",
    title: str = "",
    out_path: str | None = None,
) -> list[str]:
    """Generate music and download. Returns list of saved file paths."""

    print(f"Generating: '{prompt[:70]}'{'...' if len(prompt) > 70 else ''}")
    print(f"Mode: {'instrumental' if instrumental else 'with vocals'} | Model: {model}")

    payload = {
        "generation_type": "TEXT",
        "make_instrumental": instrumental,
        "mv": model,
        "prompt": prompt if custom else "",
        "gpt_description_prompt": "" if custom else prompt,
        "tags": tags or "",
        "title": title or "",
        "negative_tags": "",
        "override_fields": [],
        "persona_id": None,
        "metadata": {"web_client_pathname": "/create", "is_max_mode": False},
        "cover_audio_id": None,
        "cover_clip_id": None,
        "continue_at": None,
        "continue_clip_id": None,
    }

    headers = _headers(content_type=True)
    resp = requests.post(f"{SUNO_BASE}/api/generate/v2-web/", headers=headers, json=payload, timeout=30)

    # Some backends require a token field — retry once with it
    if resp.status_code == 422 and "Token validation failed" in resp.text:
        token_val = _read_token()[len("Bearer "):].strip()
        payload["token"] = token_val
        resp = requests.post(f"{SUNO_BASE}/api/generate/v2-web/", headers=headers, json=payload, timeout=30)

    if resp.status_code == 401:
        print("Auth failed (401). Token expired. Re-run: python3 generate.py --set-token \"Bearer <new_token>\"")
        return []

    if resp.status_code != 200:
        print(f"Generation failed ({resp.status_code}): {resp.text[:300]}")
        return []

    clips = resp.json().get("clips", [])
    if not clips:
        print(f"No clips returned: {resp.text[:200]}")
        return []

    song_ids = [c["id"] for c in clips]
    print(f"Submitted {len(song_ids)} track(s). Waiting for generation...")
    return _poll_and_download(song_ids, out_path)


def _poll_and_download(song_ids: list, out_path: str | None = None) -> list[str]:
    saved: list[str] = []
    feed_headers = _headers(content_type=False)

    for i in range(72):  # up to ~6 minutes
        time.sleep(5)
        r = requests.get(
            f"{SUNO_BASE}/api/feed/v2",
            params={"ids": ",".join(song_ids)},
            headers=feed_headers,
            timeout=30,
        )
        clips = r.json().get("clips", [])
        statuses = [c.get("status", "?") for c in clips]
        print(f"  [{i+1}] Status: {statuses}", end="\r", flush=True)

        done = [
            c for c in clips
            if c.get("audio_url") and c.get("status") in ("streaming", "complete")
        ]
        already_saved = {Path(p).stem for p in saved}

        for c in done:
            if c["id"][:8] in already_saved:
                continue

            if out_path and len(saved) == 0:
                dest = Path(out_path)
            else:
                dest = Path.home() / f"suno_{c['id'][:8]}.mp3"

            dest.parent.mkdir(parents=True, exist_ok=True)
            audio_data = requests.get(c["audio_url"], timeout=120)
            dest.write_bytes(audio_data.content)
            size_kb = dest.stat().st_size // 1024
            title = c.get("title", "untitled")
            print(f"\n  Saved: {dest} ({size_kb}KB) — {title}")
            saved.append(str(dest))

        if len(saved) >= len(song_ids):
            break

    if not saved:
        print("\nNo tracks downloaded. Generation may have timed out or failed.")
    return saved


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Suno AI music generation (personal use only — see Suno TOS)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 generate.py --set-token "Bearer eyJhb..."
  python3 generate.py --check
  python3 generate.py --prompt "relaxing lo-fi study music" --instrumental
  python3 generate.py --prompt "pump-up gym track" --out ~/gym_music.mp3
  python3 generate.py --prompt "[Verse]\nWoke up..." --custom --tags "pop" --title "My Song"

⚠️  Uses internal Suno API. Personal use only. Check https://suno.com/tos
        """
    )

    parser.add_argument("--set-token", metavar="TOKEN",
                        help="Save Bearer token from browser DevTools")
    parser.add_argument("--check", action="store_true",
                        help="Verify auth and show account credits")
    parser.add_argument("--prompt", help="Describe the music you want")
    parser.add_argument("--instrumental", action="store_true",
                        help="Generate without vocals")
    parser.add_argument("--custom", action="store_true",
                        help="Custom mode: prompt is treated as actual lyrics")
    parser.add_argument("--tags", default="",
                        help="Genre/style tags e.g. 'hip-hop, trap, dark'")
    parser.add_argument("--title", default="",
                        help="Song title")
    parser.add_argument("--model", default="chirp-crow",
                        help="Model name (default: chirp-crow)")
    parser.add_argument("--out", default=None,
                        help="Output file path (default: ~/suno_<id>.mp3)")

    args = parser.parse_args()

    if args.set_token:
        set_token(args.set_token)
    elif args.check:
        check()
    elif args.prompt:
        paths = generate(
            prompt=args.prompt,
            instrumental=args.instrumental,
            model=args.model,
            custom=args.custom,
            tags=args.tags,
            title=args.title,
            out_path=args.out,
        )
        for p in paths:
            print(f"SUNO_AUDIO:{p}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
