---
name: whatsapp-voice-transcriber
description: Use when a user sends a voice note and wants it transcribed, or says "transcribe this voice note", "what did I say?", "convert voice to text", or "transcribe this audio". Handles OGG, MP3, WAV, and other audio formats. Outputs transcription with content classification (Idea/Task, Draft, or Note).
---

# WhatsApp Voice Transcriber

## Overview
Transcribes voice notes using local Whisper and classifies the content by type (task/idea, draft message, or general note). Sends the result back to the configured WhatsApp target.

## Usage
```
python3 scripts/transcribe.py <audio_file_path>
```

Example:
```
python3 scripts/transcribe.py /tmp/voice_note_20260323.ogg
```

## Workflow
1. Receive the audio file path from the inbound message attachment
2. Run `scripts/transcribe.py <path>` — invokes Whisper CLI at `/opt/homebrew/bin/whisper`
3. Whisper writes transcript to `/tmp/<stem>.txt`
4. Script applies heuristic classification:
   - Keywords like "remind", "task", "idea", "build" → 💡 Idea / Task
   - Keywords like "tell", "send", "message", "reply" → ✉️ Draft
   - Everything else → 📝 Note
5. Sends formatted result to the WhatsApp target in `$WA_TARGET` (E.164 number or group JID) via `openclaw message send`
6. Print result to stdout for logging

## Scripts
- `scripts/transcribe.py` — Main entrypoint. Runs Whisper, classifies output, sends WhatsApp message. Accepts a single positional argument: path to audio file.

## Requirements
- Whisper CLI installed at `/opt/homebrew/bin/whisper` (`pip install openai-whisper`)
- OpenClaw CLI available at `/opt/homebrew/bin/openclaw`
- Python 3.10+
- Model used: `base` (fast, runs locally, no API key needed)
