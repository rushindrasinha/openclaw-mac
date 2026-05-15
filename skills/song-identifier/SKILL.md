---
name: song-identifier
description: Use when a user sends an audio file and asks "what is this song?", "what song is this?", "identify this track", "shazam this", or any variation of song/music identification. Accepts any audio file format. Returns song title, artist, album, release date, and Spotify/Apple Music streaming links via AudD API.
---

# Song Identifier

## Overview
Identifies songs from audio files using the AudD music recognition API. Returns formatted song info including streaming links for Spotify and Apple Music.

## Usage
```
python3 scripts/identify.py <audio_file_path>
```

Example:
```
python3 scripts/identify.py /tmp/audio_clip.ogg
```

## Workflow
1. Receive the audio file path from the inbound message attachment
2. Run `scripts/identify.py <path>`
3. Script POSTs the audio file to AudD API (`https://api.audd.io/`) with `return=apple_music,spotify`
4. Parse response:
   - If match found: format title, artist, album, release date, Spotify URL, Apple Music URL
   - If no match: return "No match found — song not in AudD's database"
   - If error: return descriptive error message
5. Print formatted result to stdout
6. Forward result to user

## Scripts
- `scripts/identify.py` — Single-file entrypoint. Sends audio to AudD, parses JSON response, returns formatted multi-line string with song details and streaming links.

## Requirements
- `requests` library (`pip install requests`)
- AudD API token in `AUDD_API_TOKEN` env var — free token at https://audd.io
- Internet connection
- Python 3.8+
