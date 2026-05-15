# FCPXML from Script

## Trigger
Use this skill when the user wants to:
- Create a Final Cut Pro project from a script + audio file
- Auto-generate an FCP timeline from a voiceover
- Generate FCPXML from audio with whisper timestamps
- Auto-edit video in Final Cut Pro from a script
- Build an FCP timeline where each sentence is a color-coded clip

## What It Does
Takes a script text file + audio/voiceover file and:
1. Runs Whisper to get word-level timestamps
2. Groups words into sentence blocks
3. Generates valid FCPXML 1.11 with:
   - 25fps, 1920×1080 timeline
   - Audio track on the timeline
   - Colored placeholder clips for each sentence (timed to Whisper)
   - Text overlay on each clip showing the spoken line
4. Opens the FCPXML in Final Cut Pro via osascript

## Location
`~/.openclaw/workspace/.agents/skills/fcpxml-from-script/`

## Scripts
- `scripts/generate_fcpxml.py` — main CLI

## References
- `references/fcpxml-template.md` — FCPXML 1.11 structure, time notation, element reference

## Usage

```bash
python3 ~/.openclaw/workspace/.agents/skills/fcpxml-from-script/scripts/generate_fcpxml.py \
  --script script.txt \
  --audio voiceover.mp3 \
  --output timeline.fcpxml
```

Options:
- `--no-open` — generate FCPXML but don't auto-open in FCP
- `--model` — Whisper model size: `tiny`, `base` (default), `small`, `medium`, `large`

## Requirements

```bash
pip install openai-whisper
brew install ffmpeg
# Final Cut Pro must be installed at /Applications/Final Cut Pro.app
```

## Notes
- Whisper must be installed: `pip install openai-whisper` (or `brew install whisper`)
- Uses `base` model by default — use `--model small` for better accuracy
- Each sentence becomes one colored placeholder clip in FCP
- Audio is imported as a dialogue track
- FCPXML 1.11 requires FCP 10.6.5+
- See `references/fcpxml-template.md` for the full XML structure
