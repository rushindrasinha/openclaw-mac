#!/usr/bin/env python3
"""
song_identify.py — Identify a song from an audio file using AudD API.

Usage:
    python3 song_identify.py <audio_file_path>

Set AUDD_API_TOKEN in your environment (get a free token at https://audd.io).

Returns formatted song info to stdout.
"""

import os
import sys
import json
import requests

AUDD_API_TOKEN = os.environ.get("AUDD_API_TOKEN", "")
AUDD_API_URL = "https://api.audd.io/"

if not AUDD_API_TOKEN:
    print("❌ AUDD_API_TOKEN not set. Get a token at https://audd.io and export AUDD_API_TOKEN=...")
    sys.exit(1)


def identify_song(file_path: str) -> str:
    """Send audio file to AudD and return formatted result."""
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                AUDD_API_URL,
                data={
                    "api_token": AUDD_API_TOKEN,
                    "return": "apple_music,spotify",
                },
                files={"file": f},
                timeout=30,
            )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        return "❌ AudD timed out. Try again."
    except requests.exceptions.RequestException as e:
        return f"❌ Request failed: {e}"
    except json.JSONDecodeError:
        return "❌ Unexpected response from AudD."

    if data.get("status") != "success":
        return f"❌ AudD error: {data.get('error', {}).get('error_message', 'Unknown error')}"

    result = data.get("result")
    if not result:
        return "🎵 No match found — song not in AudD's database."

    # Core info
    title = result.get("title", "Unknown")
    artist = result.get("artist", "Unknown")
    album = result.get("album", "")
    release_date = result.get("release_date", "")

    lines = [f"🎵 *{title}*", f"👤 {artist}"]

    if album:
        lines.append(f"💿 {album}")
    if release_date:
        lines.append(f"📅 {release_date}")

    # Spotify link
    spotify = result.get("spotify")
    if spotify and isinstance(spotify, dict):
        ext_urls = spotify.get("external_urls", {})
        spotify_url = ext_urls.get("spotify")
        if spotify_url:
            lines.append(f"🟢 Spotify: {spotify_url}")

    # Apple Music link
    apple = result.get("apple_music")
    if apple and isinstance(apple, dict):
        apple_url = apple.get("url")
        if apple_url:
            lines.append(f"🍎 Apple Music: {apple_url}")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 song_identify.py <audio_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    print(identify_song(file_path))
