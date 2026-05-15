# suno-music-gen

**Trigger:** generate AI music, background music for videos, create a song, instrumental track, make music with AI, Suno, AI-generated music, music for content

## What This Does

Generates AI music tracks (with or without vocals) from text prompts using Suno AI. Good for background music, intro/outro tracks, content scoring, or creating original songs.

⚠️ **WARNING:** This uses Suno's internal browser API — not an official public API. For personal use only. Review [Suno's Terms of Service](https://suno.com/tos) before using commercially.

---

## One-Time Setup

1. Open [https://suno.com/create](https://suno.com/create) in Chrome and sign in
2. Open DevTools → Network tab (F12 → Network)
3. Generate any song to trigger network traffic
4. Find a request to `studio-api.prod.suno.com` → click it → Headers tab
5. Copy the `Authorization` header value (starts with `Bearer eyJ...`)
6. Run:

```bash
python3 ~/.openclaw/workspace/.agents/skills/suno-music-gen/scripts/generate.py --set-token "Bearer <paste_here>"
```

Verify it works:
```bash
python3 ~/.openclaw/workspace/.agents/skills/suno-music-gen/scripts/generate.py --check
# Output: Connected to Suno | Plan: Pro | Credits remaining: 500
```

Token is saved to `~/.suno_token` (chmod 600).

---

## Generate Music

### Background / instrumental track

```bash
python3 ~/.openclaw/workspace/.agents/skills/suno-music-gen/scripts/generate.py \
    --prompt "chill lo-fi hip-hop, study beats, warm piano, soft drums" \
    --instrumental \
    --out ~/background_track.mp3
```

### With vocals

```bash
python3 ~/.openclaw/workspace/.agents/skills/suno-music-gen/scripts/generate.py \
    --prompt "upbeat motivational pop song about chasing your dreams" \
    --out ~/vocal_track.mp3
```

### Custom mode (you write the lyrics)

```bash
python3 ~/.openclaw/workspace/.agents/skills/suno-music-gen/scripts/generate.py \
    --prompt "[Verse 1]\nWoke up early, sun is rising\nGot that fire, keep on climbing\n[Chorus]\nWe're unstoppable tonight" \
    --custom \
    --tags "pop, upbeat, energetic" \
    --title "Unstoppable" \
    --out ~/my_song.mp3
```

### Options

| Flag | Description |
|------|-------------|
| `--prompt` | Describe the music (style, mood, genre, instruments) |
| `--instrumental` | Generate without vocals |
| `--custom` | Treat prompt as lyrics (custom mode) |
| `--tags` | Genre tags e.g. `"hip-hop, dark, trap"` |
| `--title` | Song title |
| `--model` | Model name (default: `chirp-crow`) |
| `--out` | Save path (default: `~/suno_<id>.mp3`) |

---

## Prompt Tips

- **Be specific:** `"dark cinematic orchestral, strings, tension, no drums"` works better than `"cinematic music"`
- **Mood + genre + instruments:** `"relaxing jazz piano, late night, mellow saxophone, brushed drums"`
- **Content scoring:** `"energetic gaming montage music, fast-paced EDM, synth drops, 130bpm"`
- **Intros/outros:** `"short 15-second podcast intro, upbeat, tech-forward, logo-reveal feel"`

---

## Token Expiry

Bearer tokens expire (typically after 30–60 min). If you get a 401 error:

1. Go back to Chrome → DevTools → copy a fresh `Authorization` header from any Suno request
2. Re-run: `python3 generate.py --set-token "Bearer <new_token>"`

---

## Output

- Two tracks generated per request (Suno's default)
- Saved as MP3 to `--out` path, or `~/suno_<id>.mp3` if not specified
- Prints `SUNO_AUDIO:<path>` on completion for piping/scripting

---

## Requirements

- Python 3.10+
- `pip install requests`
- Suno account (free or paid) at https://suno.com

## Files

- `scripts/generate.py` — main CLI script
