# YouTube Shorts Pipeline — Configuration Reference

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Gemini API key for script generation. Falls back to `~/.openclaw/credentials/nanobanana.key` |
| `ELEVENLABS_API_KEY` | Yes | ElevenLabs API key for voiceover generation |
| `ELEVENLABS_VOICE_ID` | No | Override voice ID (default: `pNInz6obpgDQGcFmaJgB` — Adam) |
| `REPLICATE_API_TOKEN` | Yes | Replicate token for Kling 3.0 b-roll generation |
| `YOUTUBE_CREDENTIALS_PATH` | Yes (upload only) | Path to YouTube OAuth credentials JSON |
| `SHORTS_DRAFTS_DIR` | No | Override draft save directory (default: `~/shorts_drafts`) |

## Draft JSON Format

Drafts are saved to `~/shorts_drafts/<id>.json`. Structure:

```json
{
  "id": "1711234567",
  "topic": "SpaceX launches reusable booster",
  "status": "draft | produced | uploaded",
  "created_at": 1711234567,

  "title": "YouTube video title (max 70 chars)",
  "script": "45-60 second voiceover script text",
  "broll_prompts": [
    "Cinematic scene description 1",
    "Cinematic scene description 2",
    "Cinematic scene description 3"
  ],
  "music_brief": "Music style description for background track",
  "description": "YouTube video description with hashtags",
  "caption": "Social cross-post caption with hashtags",
  "thumbnail_prompt": "16:9 thumbnail image description",

  "video_path": "/Users/.../shorts_drafts/1711234567_final.mp4",
  "youtube_url": "https://youtu.be/VIDEO_ID"
}
```

## Directory Layout

```
~/shorts_drafts/
  1711234567.json          ← draft metadata
  1711234567_final.mp4     ← produced video
  work/
    1711234567/
      voiceover.mp3        ← ElevenLabs audio
      voiceover.words.json ← word-level timestamps
      broll_1.mp4          ← Kling clip 1
      broll_2.mp4          ← Kling clip 2
      broll_3.mp4          ← Kling clip 3
      proc_1.mp4           ← processed/looped clip 1
      proc_2.mp4           ← processed/looped clip 2
      proc_3.mp4           ← processed/looped clip 3
      final.mp4            ← assembled before copy
```

## Workflow

```
python3 pipeline.py draft --topic "Your topic here"
  → saves ~/shorts_drafts/<id>.json

# Review draft, optionally edit the JSON to tweak script/prompts

python3 pipeline.py produce --id <id>
  → generates voiceover + b-roll → assembles final.mp4

python3 pipeline.py upload --id <id>
  → uploads to YouTube → writes youtube_url to draft JSON
```

## Fallbacks

- **No ELEVENLABS_API_KEY**: Falls back to macOS `say` command (Samantha voice)
- **No REPLICATE_API_TOKEN**: Generates colored placeholder clips via FFmpeg
- **No YOUTUBE_CREDENTIALS_PATH**: Upload step raises an error with clear message

## YouTube OAuth Setup

1. Create OAuth 2.0 credentials in Google Cloud Console
2. Enable YouTube Data API v3
3. Download credentials JSON
4. Run auth flow once: `python3 -c "from google_auth_oauthlib.flow import InstalledAppFlow; flow = InstalledAppFlow.from_client_secrets_file('credentials.json', ['https://www.googleapis.com/auth/youtube.upload']); creds = flow.run_local_server(); open('token.json','w').write(creds.to_json())"`
5. Set `YOUTUBE_CREDENTIALS_PATH=~/path/to/token.json`
