#!/usr/bin/env python3
"""
generate_fcpxml.py — Generate Final Cut Pro XML from a script + audio file
==========================================================================
Uses Whisper to get word-level timestamps, then generates a valid FCPXML 1.11
project with:
  - 25fps timeline
  - Audio track (your voiceover)
  - Colored placeholder generator clips timed to each sentence
  - Text overlay with the spoken line on each clip

Then opens the result in Final Cut Pro via osascript.

Usage:
  python3 generate_fcpxml.py --script script.txt --audio voiceover.mp3 --output timeline.fcpxml

Requirements:
  pip install openai-whisper
  brew install ffmpeg
  Final Cut Pro installed at /Applications/Final Cut Pro.app
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


# ── Color palette for sentence clips ──────────────────────────────────────────
CLIP_COLORS = [
    "0.5 0.2 0.8 1",   # Purple
    "0.2 0.6 0.9 1",   # Blue
    "0.9 0.4 0.2 1",   # Orange
    "0.2 0.8 0.4 1",   # Green
    "0.8 0.2 0.4 1",   # Red
    "0.9 0.8 0.1 1",   # Yellow
    "0.4 0.8 0.8 1",   # Teal
    "0.8 0.5 0.9 1",   # Lavender
]

FPS = 25
FRAME_DUR = "1/25s"
TIMELINE_FORMAT_ID = "r1"
AUDIO_ASSET_ID = "r2"

# ── Frame math ────────────────────────────────────────────────────────────────

def seconds_to_frames(seconds: float) -> int:
    return int(round(seconds * FPS))


def frames_to_fcptime(frames: int) -> str:
    """Convert frame count to FCPXML rational time string."""
    return f"{frames * (3600 * FPS) // (FPS)}s" if False else f"{frames}/{FPS}s"


def secs_to_fcptime(seconds: float) -> str:
    """Convert seconds to FCPXML rational time (e.g. '125/25s')."""
    frames = seconds_to_frames(seconds)
    return f"{frames}/{FPS}s"


# ── Whisper transcription ─────────────────────────────────────────────────────

def transcribe_with_whisper(audio_path: Path) -> dict:
    """Run Whisper with word-level timestamps. Returns raw JSON output."""
    print(f"  Running Whisper on: {audio_path.name}", flush=True)

    # Use a temp dir for output
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [
                "whisper", str(audio_path),
                "--output_format", "json",
                "--word_timestamps", "True",
                "--model", "base",
                "--output_dir", tmpdir,
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            print(f"  Whisper stderr: {result.stderr}", flush=True)
            raise RuntimeError(f"Whisper failed: {result.stderr}")

        # Find the output JSON
        json_files = list(Path(tmpdir).glob("*.json"))
        if not json_files:
            raise FileNotFoundError("Whisper did not produce a JSON output file")

        data = json.loads(json_files[0].read_text())

    print(f"  Transcribed: {len(data.get('segments', []))} segments", flush=True)
    return data


def extract_sentences(whisper_data: dict) -> list[dict]:
    """
    Extract sentence-level blocks with start/end times from Whisper output.
    Returns list of {text, start, end} dicts.
    """
    sentences = []
    current_words = []
    current_start = None
    current_end = None

    for segment in whisper_data.get("segments", []):
        words = segment.get("words", [])
        if not words:
            # Segment without word timing — treat whole segment as one sentence
            sentences.append({
                "text": segment["text"].strip(),
                "start": segment["start"],
                "end": segment["end"],
            })
            continue

        for word_info in words:
            word = word_info.get("word", "").strip()
            w_start = word_info.get("start", current_end or 0)
            w_end = word_info.get("end", w_start + 0.2)

            if current_start is None:
                current_start = w_start

            current_words.append(word)
            current_end = w_end

            # Split on sentence-ending punctuation
            if word.rstrip().endswith((".", "!", "?", "...", "।")):
                if current_words:
                    sentences.append({
                        "text": " ".join(current_words).strip(),
                        "start": current_start,
                        "end": current_end,
                    })
                    current_words = []
                    current_start = None
                    current_end = None

    # Flush remaining words
    if current_words and current_start is not None:
        sentences.append({
            "text": " ".join(current_words).strip(),
            "start": current_start,
            "end": current_end,
        })

    return sentences


# ── FCPXML Generation ─────────────────────────────────────────────────────────

def escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))


def get_audio_duration(audio_path: Path) -> float:
    """Get duration in seconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(audio_path)],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return float(result.stdout.strip())


def generate_fcpxml(
    script_path: Path,
    audio_path: Path,
    output_path: Path,
    sentences: list[dict],
    audio_duration: float,
) -> None:
    """Generate FCPXML 1.11 file."""

    total_frames = seconds_to_frames(audio_duration)
    total_duration = secs_to_fcptime(audio_duration)
    audio_abs = str(audio_path.resolve())

    # Determine audio format from extension
    ext = audio_path.suffix.lower()
    audio_format = "mp3" if ext == ".mp3" else "aac" if ext in (".m4a", ".aac") else "wav"

    lines = []

    # ── Header ────────────────────────────────────────────────────────────────
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<!DOCTYPE fcpxml>')
    lines.append('<fcpxml version="1.11">')
    lines.append('  <resources>')

    # Timeline format (25fps, 1920x1080)
    lines.append(f'    <format id="{TIMELINE_FORMAT_ID}" name="FFVideoFormat1080p25" '
                 f'frameDuration="{FRAME_DUR}" width="1920" height="1080" '
                 f'colorSpace="1-1-1 (Rec. 709)"/>')

    # Audio asset
    lines.append(f'    <asset id="{AUDIO_ASSET_ID}" name="{escape_xml(audio_path.stem)}" '
                 f'src="file://{audio_abs}" start="0s" duration="{total_duration}" '
                 f'hasAudio="1" audioSources="1" audioChannels="2" audioRate="44100"/>')

    lines.append('  </resources>')
    lines.append('  <library>')
    lines.append(f'    <event name="{escape_xml(script_path.stem)}">')
    lines.append(f'    <project name="{escape_xml(script_path.stem)}" uid="{uuid.uuid4()}">')
    lines.append(f'      <sequence duration="{total_duration}" format="{TIMELINE_FORMAT_ID}" '
                 f'tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="44100">')
    lines.append('        <spine>')

    # ── Sentence clips ────────────────────────────────────────────────────────
    for i, sentence in enumerate(sentences):
        start = sentence["start"]
        end = sentence["end"]
        duration = max(end - start, 1.0 / FPS)
        color = CLIP_COLORS[i % len(CLIP_COLORS)]
        text = escape_xml(sentence["text"])
        offset_time = secs_to_fcptime(start)
        dur_time = secs_to_fcptime(duration)
        clip_name = escape_xml(f"Clip {i+1}: {sentence['text'][:40]}")

        # Generator clip (colored placeholder)
        lines.append(f'          <gap name="{clip_name}" offset="{offset_time}" '
                     f'duration="{dur_time}" start="0s">')

        # Colored background using custom generator
        lines.append(f'            <video name="Color Solid" offset="0s" duration="{dur_time}" '
                     f'ref="{TIMELINE_FORMAT_ID}">')
        lines.append(f'              <param name="Color" value="{color}"/>')
        lines.append(f'            </video>')

        # Text overlay with spoken line
        lines.append(f'            <title name="{clip_name}" offset="0s" duration="{dur_time}" '
                     f'ref="{TIMELINE_FORMAT_ID}">')
        lines.append(f'              <text>')
        lines.append(f'                <text-style ref="ts{i}">{text}</text-style>')
        lines.append(f'              </text>')
        lines.append(f'              <text-style-def id="ts{i}">')
        lines.append(f'                <text-style font="Helvetica Neue" fontSize="48" '
                     f'fontFace="Bold" fontColor="1 1 1 1" alignment="center" '
                     f'shadowColor="0 0 0 0.8" shadowOffset="5 315" shadowBlurRadius="5"/>')
        lines.append(f'              </text-style-def>')
        lines.append(f'            </title>')

        lines.append(f'          </gap>')

    lines.append('        </spine>')

    # ── Audio track ───────────────────────────────────────────────────────────
    lines.append(f'        <audio lane="-1" offset="0s" ref="{AUDIO_ASSET_ID}" '
                 f'duration="{total_duration}" role="dialogue"/>')

    lines.append('      </sequence>')
    lines.append('    </project>')
    lines.append('    </event>')
    lines.append('  </library>')
    lines.append('</fcpxml>')

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  FCPXML saved: {output_path} ({output_path.stat().st_size // 1024}KB)", flush=True)


def open_in_fcp(fcpxml_path: Path):
    """Open the FCPXML file in Final Cut Pro via osascript."""
    fcp_path = "/Applications/Final Cut Pro.app"
    if not Path(fcp_path).exists():
        print(f"  Final Cut Pro not found at {fcp_path} — skipping auto-open", flush=True)
        return

    print(f"  Opening in Final Cut Pro...", flush=True)
    script = f'''
tell application "Final Cut Pro"
    activate
    open POSIX file "{fcpxml_path.resolve()}"
end tell
'''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        print(f"  Opened in Final Cut Pro", flush=True)
    else:
        print(f"  osascript error: {result.stderr}", flush=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate Final Cut Pro XML from a script + audio file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--script", required=True, type=Path, help="Script text file (.txt)")
    parser.add_argument("--audio", required=True, type=Path, help="Audio/voiceover file (.mp3, .m4a, .wav)")
    parser.add_argument("--output", required=True, type=Path, help="Output FCPXML file (.fcpxml)")
    parser.add_argument("--no-open", action="store_true", help="Don't open in Final Cut Pro after generating")
    parser.add_argument("--model", default="base", help="Whisper model size (tiny/base/small/medium/large)")
    args = parser.parse_args()

    # Validate inputs
    if not args.script.exists():
        print(f"Error: Script file not found: {args.script}", flush=True)
        sys.exit(1)
    if not args.audio.exists():
        print(f"Error: Audio file not found: {args.audio}", flush=True)
        sys.exit(1)

    print(f"\n{'═'*50}", flush=True)
    print(f"  FCPXML Generator", flush=True)
    print(f"  Script: {args.script.name}", flush=True)
    print(f"  Audio:  {args.audio.name}", flush=True)
    print(f"  Output: {args.output}", flush=True)
    print(f"{'═'*50}\n", flush=True)

    # Step 1: Get audio duration
    print("  [1/4] Getting audio duration...", flush=True)
    audio_duration = get_audio_duration(args.audio)
    print(f"  Duration: {audio_duration:.2f}s", flush=True)

    # Step 2: Transcribe with Whisper
    print("\n  [2/4] Transcribing with Whisper (word-level timestamps)...", flush=True)
    whisper_data = transcribe_with_whisper(args.audio)

    # Step 3: Extract sentences
    print("\n  [3/4] Extracting sentence blocks...", flush=True)
    sentences = extract_sentences(whisper_data)
    print(f"  Found {len(sentences)} sentences:", flush=True)
    for i, s in enumerate(sentences):
        print(f"    [{s['start']:.2f}s → {s['end']:.2f}s] {s['text'][:60]}", flush=True)

    # Step 4: Generate FCPXML
    print(f"\n  [4/4] Generating FCPXML 1.11...", flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    generate_fcpxml(args.script, args.audio, args.output, sentences, audio_duration)

    # Open in FCP
    if not args.no_open:
        open_in_fcp(args.output)

    print(f"\n{'═'*50}", flush=True)
    print(f"  Done! FCPXML at: {args.output.resolve()}", flush=True)
    print(f"  Import manually: File → Import → XML in Final Cut Pro", flush=True)
    print(f"{'═'*50}\n", flush=True)


if __name__ == "__main__":
    main()
