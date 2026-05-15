# YouTube Shorts Pipeline

## Trigger
Use this skill when the user wants to:
- Create YouTube Shorts automatically from a topic or headline
- Run an end-to-end video pipeline from topic to upload
- Generate AI-powered short-form video content (9:16)
- Create voiceover + b-roll + assembled vertical video
- Automate YouTube Shorts creation with AI

## What It Does
End-to-end pipeline for generating YouTube Shorts:
1. **Draft** — Gemini generates script, b-roll prompts, title, description, caption
2. **Produce** — ElevenLabs voiceover + Replicate/Kling 3.0 b-roll + FFmpeg assembly
3. **Upload** — pushes to YouTube via OAuth

## Location
`~/.openclaw/workspace/.agents/skills/youtube-shorts-pipeline/`

## Scripts
- `scripts/pipeline.py` — main pipeline CLI

## References
- `references/config.md` — environment variables, draft JSON format, directory layout

## Usage

```bash
# Step 1: Generate draft (script + metadata)
python3 ~/.openclaw/workspace/.agents/skills/youtube-shorts-pipeline/scripts/pipeline.py draft --topic "Your topic here"

# Step 2: Review draft at ~/shorts_drafts/<id>.json, then produce
python3 ~/.openclaw/workspace/.agents/skills/youtube-shorts-pipeline/scripts/pipeline.py produce --id <id>

# Step 3: Upload to YouTube
python3 ~/.openclaw/workspace/.agents/skills/youtube-shorts-pipeline/scripts/pipeline.py upload --id <id>
```

## Required Environment Variables
- `GEMINI_API_KEY` — script generation (falls back to `~/.openclaw/credentials/nanobanana.key`)
- `ELEVENLABS_API_KEY` — voiceover
- `REPLICATE_API_TOKEN` — Kling 3.0 b-roll video generation
- `YOUTUBE_CREDENTIALS_PATH` — YouTube OAuth token JSON (upload step only)

## Notes
- Drafts saved to `~/shorts_drafts/<id>.json`
- All steps are idempotent — re-running produce reuses existing clips
- Fallbacks: macOS `say` if no ElevenLabs key, colored placeholder clips if no Replicate token
- See `references/config.md` for full configuration and YouTube OAuth setup
