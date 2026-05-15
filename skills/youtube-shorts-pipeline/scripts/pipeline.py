#!/usr/bin/env python3
"""
YouTube Shorts Pipeline — AI-Native End-to-End Video Creation
=============================================================
Generalized pipeline for creating YouTube Shorts from any topic.

Flow:
  draft   → AI generates script + b-roll prompts + metadata
            → saves to ~/shorts_drafts/<id>.json
            → prints draft for review

  produce → generates voiceover (ElevenLabs) + b-roll (Replicate/Kling)
            + background music → assembles 9:16 vertical video via FFmpeg

  upload  → pushes to YouTube via oauth credentials

Usage:
  python3 pipeline.py draft --topic "SpaceX launches reusable booster"
  python3 pipeline.py produce --id <id>
  python3 pipeline.py upload --id <id>

Environment Variables:
  ELEVENLABS_API_KEY       — ElevenLabs API key
  REPLICATE_API_TOKEN      — Replicate API token (for Kling 3.0 b-roll)
  YOUTUBE_CREDENTIALS_PATH — Path to YouTube OAuth credentials JSON
  GEMINI_API_KEY           — Gemini API key (for script generation)
  SHORTS_DRAFTS_DIR        — Override draft save directory (default: ~/shorts_drafts)
"""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import requests

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPTS_DIR  = Path(__file__).parent
DRAFTS_DIR   = Path(os.environ.get("SHORTS_DRAFTS_DIR", str(Path.home() / "shorts_drafts"))).expanduser()
WORK_DIR     = DRAFTS_DIR / "work"

# ── Video Config ──────────────────────────────────────────────────────────────
SHORT_WIDTH  = 1080
SHORT_HEIGHT = 1920
VIDEO_FPS    = 30

# ── ElevenLabs ────────────────────────────────────────────────────────────────
DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"   # Adam — change via ELEVENLABS_VOICE_ID env
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)


def log(msg: str):
    print(f"  {msg}", flush=True)


def step(n: int, title: str):
    print(f"\n{'─'*50}", flush=True)
    print(f"  Step {n} — {title}", flush=True)
    print(f"{'─'*50}", flush=True)


def run_cmd(cmd, check=True, capture=False, **kwargs):
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
        if check and result.returncode != 0:
            raise RuntimeError(f"Command failed: {result.stderr}")
        return result
    subprocess.run(cmd, check=check, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Script + Metadata Generation (Gemini)
# ─────────────────────────────────────────────────────────────────────────────

def _get_gemini_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    fallback = Path.home() / ".openclaw/credentials/nanobanana.key"
    if fallback.exists():
        return fallback.read_text().strip()
    raise EnvironmentError("GEMINI_API_KEY not set. Set it in your environment.")


def generate_draft(topic: str) -> dict:
    """Generate script, b-roll prompts, and metadata for a YouTube Short."""
    step(1, "Script + Metadata Generation")

    key = _get_gemini_key()
    import urllib.request

    prompt = f"""You are a YouTube Shorts scriptwriter. Create a complete content package for a 45-60 second vertical Short about:

Topic: "{topic}"

Return ONLY a valid JSON object with these fields:

{{
  "title": "YouTube title (max 70 chars, SEO-optimized, punchy)",
  "script": "45-60 second voiceover script (80-100 words). Hook in first 3 seconds. Clear, conversational, engaging. End with a call-to-action to like and subscribe.",
  "broll_prompts": [
    "Cinematic 9:16 vertical video scene description. Explicit camera motion, lighting, mood. No text overlays, no UI, no faces unless requested. 3-5 seconds each.",
    "Second scene — different angle or moment",
    "Third scene — climactic or resolution beat"
  ],
  "music_brief": "Music style description: tempo, mood, genre (e.g. 'upbeat electronic, fast tempo, energetic')",
  "description": "YouTube description (2-3 sentences + relevant hashtags). SEO-optimized.",
  "caption": "Short social caption (1-2 punchy lines + 3-5 hashtags) for Instagram/TikTok cross-post.",
  "thumbnail_prompt": "16:9 thumbnail description: bold visual, high contrast, minimal text space"
}}

Rules:
- Script must flow naturally as voiceover (not written prose)
- B-roll prompts must be cinematic video descriptions with motion (not static images)
- Every field must be populated
- Return ONLY the JSON object, no markdown fences
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 2000},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = "\n".join(l for l in raw.splitlines() if not l.startswith("```")).strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}") + 1
        result = json.loads(raw[start:end])

    log(f"Script: {result['script'][:80]}...")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — ElevenLabs Voiceover
# ─────────────────────────────────────────────────────────────────────────────

def generate_voiceover(script: str, work_dir: Path) -> tuple[Path, list]:
    """Generate voiceover MP3 + word timings via ElevenLabs."""
    step(2, "ElevenLabs Voiceover")
    import base64

    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    out_path = work_dir / "voiceover.mp3"
    words_path = work_dir / "voiceover.words.json"

    if out_path.exists() and out_path.stat().st_size > 5000:
        log("Reusing existing voiceover")
        word_timings = json.loads(words_path.read_text()) if words_path.exists() else []
        return out_path, word_timings

    if not api_key:
        log("ELEVENLABS_API_KEY not set — using macOS say fallback")
        _say_fallback(script, out_path)
        return out_path, []

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/with-timestamps"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "text": script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    audio_bytes = base64.b64decode(data["audio_base64"])
    out_path.write_bytes(audio_bytes)

    alignment = data.get("alignment", {})
    characters = alignment.get("characters", [])
    char_starts = alignment.get("character_start_times_seconds", [])
    char_ends = alignment.get("character_end_times_seconds", [])

    word_timings = _chars_to_words(characters, char_starts, char_ends)
    words_path.write_text(json.dumps(word_timings, indent=2))

    log(f"Voiceover: {out_path.stat().st_size // 1024}KB, {len(word_timings)} words")
    return out_path, word_timings


def _chars_to_words(chars, starts, ends) -> list:
    words, current, w_start, w_end = [], [], None, None
    for i, ch in enumerate(chars):
        if ch == " ":
            if current:
                words.append({"word": "".join(current), "start": round(w_start, 3), "end": round(w_end, 3)})
                current, w_start, w_end = [], None, None
        else:
            current.append(ch)
            if w_start is None:
                w_start = starts[i]
            w_end = ends[i]
    if current and w_start is not None:
        words.append({"word": "".join(current), "start": round(w_start, 3), "end": round(w_end, 3)})
    return words


def _say_fallback(script: str, out_path: Path):
    aiff = out_path.with_suffix(".aiff")
    subprocess.run(["say", "-v", "Samantha", "-r", "175", "-o", str(aiff), script], check=True)
    run_cmd(["ffmpeg", "-y", "-i", str(aiff), "-c:a", "libmp3lame", "-q:a", "4", str(out_path)], capture=True)
    aiff.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Replicate B-Roll Generation (Kling 3.0)
# ─────────────────────────────────────────────────────────────────────────────

def generate_broll(prompts: list, work_dir: Path) -> list[Path]:
    """Generate b-roll video clips via Replicate (Kling 3.0)."""
    step(3, "B-Roll Generation (Replicate / Kling 3.0)")

    token = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    existing = [work_dir / f"broll_{i+1}.mp4" for i in range(len(prompts))]
    if all(p.exists() and p.stat().st_size > 50000 for p in existing):
        log("Reusing existing b-roll clips")
        return existing

    if not token:
        log("REPLICATE_API_TOKEN not set — generating placeholder clips via FFmpeg")
        paths = []
        for i, prompt in enumerate(prompts):
            out = work_dir / f"broll_{i+1}.mp4"
            _placeholder_clip(out, prompt, i)
            paths.append(out)
        return paths

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    prediction_ids = []

    # Submit all jobs
    for i, prompt in enumerate(prompts):
        body = {
            "version": "kling-v3-0",  # Kling 3.0 via Replicate
            "input": {
                "prompt": prompt,
                "aspect_ratio": "9:16",
                "duration": 5,
            },
        }
        resp = requests.post(
            "https://api.replicate.com/v1/models/kuaishou/kling-video/predictions",
            headers=headers,
            json=body,
            timeout=30,
        )
        if resp.status_code not in (200, 201):
            log(f"  Replicate submit failed for clip {i+1}: {resp.text[:200]}")
            prediction_ids.append(None)
            continue
        pred_id = resp.json()["id"]
        prediction_ids.append(pred_id)
        log(f"  Submitted clip {i+1}: {pred_id[:12]}...")

    # Poll until all complete (10 min timeout)
    TIMEOUT = 600
    deadline = time.time() + TIMEOUT
    completed = {}  # pred_id → url

    while len(completed) < sum(1 for p in prediction_ids if p) and time.time() < deadline:
        time.sleep(5)
        for pred_id in prediction_ids:
            if pred_id is None or pred_id in completed:
                continue
            r = requests.get(f"https://api.replicate.com/v1/predictions/{pred_id}", headers=headers, timeout=15)
            data = r.json()
            status = data.get("status", "")
            if status == "succeeded":
                output = data.get("output")
                url = output[0] if isinstance(output, list) else output
                completed[pred_id] = url
                log(f"  ✓ Clip {prediction_ids.index(pred_id)+1} ready")
            elif status == "failed":
                raise RuntimeError(f"Replicate prediction {pred_id} failed: {data.get('error')}")

    # Download clips
    paths = []
    for i, pred_id in enumerate(prediction_ids):
        out = work_dir / f"broll_{i+1}.mp4"
        if pred_id and pred_id in completed:
            dl_url = completed[pred_id]
            with requests.get(dl_url, stream=True, timeout=120) as r:
                r.raise_for_status()
                out.write_bytes(r.content)
            log(f"  Downloaded broll_{i+1}.mp4 ({out.stat().st_size // 1024}KB)")
        else:
            _placeholder_clip(out, prompts[i], i)
        paths.append(out)

    return paths


def _placeholder_clip(out_path: Path, prompt: str, index: int):
    """Generate a colored placeholder clip when no API key available."""
    colors = ["0x1a1a2e", "0x16213e", "0x0f3460"]
    color = colors[index % len(colors)]
    run_cmd([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c={color}:s={SHORT_WIDTH}x{SHORT_HEIGHT}:r={VIDEO_FPS}",
        "-t", "5", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        str(out_path),
    ], capture=True)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — FFmpeg Assembly
# ─────────────────────────────────────────────────────────────────────────────

def assemble_video(broll_clips: list[Path], voiceover: Path, work_dir: Path) -> Path:
    """Assemble b-roll clips + voiceover into final 9:16 MP4."""
    step(4, "FFmpeg Assembly")

    # Get VO duration
    result = run_cmd(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(voiceover)],
        capture=True,
    )
    vo_duration = float(result.stdout.strip())
    seg_dur = vo_duration / len(broll_clips)
    log(f"VO: {vo_duration:.1f}s | {len(broll_clips)} clips × {seg_dur:.1f}s each")

    # Loop/trim each clip to segment duration
    processed = []
    for i, clip in enumerate(broll_clips):
        out = work_dir / f"proc_{i+1}.mp4"
        run_cmd([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(clip),
            "-t", str(seg_dur),
            "-vf", f"scale={SHORT_WIDTH}:{SHORT_HEIGHT}:force_original_aspect_ratio=increase,crop={SHORT_WIDTH}:{SHORT_HEIGHT},fps={VIDEO_FPS}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-an",
            str(out),
        ], capture=True)
        processed.append(out)
        log(f"  Processed clip {i+1}")

    # Concat
    concat_file = work_dir / "concat.txt"
    concat_file.write_text("\n".join(f"file '{p}'" for p in processed))
    concat_raw = work_dir / "concat_raw.mp4"
    run_cmd(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(concat_raw)], capture=True)

    # Merge with audio
    final = work_dir / "final.mp4"
    run_cmd([
        "ffmpeg", "-y",
        "-i", str(concat_raw),
        "-i", str(voiceover),
        "-t", str(vo_duration),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(final),
    ], capture=True)

    size_mb = final.stat().st_size / (1024 * 1024)
    log(f"Final: {final.name} ({size_mb:.1f}MB)")
    return final


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — YouTube Upload
# ─────────────────────────────────────────────────────────────────────────────

def upload_to_youtube(video_path: Path, title: str, description: str, tags: list) -> str:
    """Upload video to YouTube. Returns video URL."""
    step(5, "YouTube Upload")

    creds_path = os.environ.get("YOUTUBE_CREDENTIALS_PATH", "").strip()
    if not creds_path:
        raise EnvironmentError("YOUTUBE_CREDENTIALS_PATH not set")

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = Credentials.from_authorized_user_file(creds_path)
    youtube = build("youtube", "v3", credentials=creds)

    title = (title[:67] + "...") if len(title) > 70 else title

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",  # People & Blogs
        },
        "status": {"privacyStatus": "public"},
    }

    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True, chunksize=50 * 1024 * 1024)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log(f"  Upload: {int(status.progress() * 100)}%")

    video_id = response["id"]
    url = f"https://youtu.be/{video_id}"
    log(f"Uploaded: {url}")
    return url


# ─────────────────────────────────────────────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────────────────────────────────────────────

def cmd_draft(topic: str):
    t0 = time.time()
    draft_id = str(int(time.time()))

    print(f"\n{'═'*50}", flush=True)
    print(f"  YouTube Shorts Pipeline — Draft", flush=True)
    print(f"  Topic: {topic}", flush=True)
    print(f"{'═'*50}", flush=True)

    draft_data = generate_draft(topic)
    draft_data["topic"] = topic
    draft_data["id"] = draft_id
    draft_data["status"] = "draft"
    draft_data["created_at"] = int(time.time())

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    draft_path = DRAFTS_DIR / f"{draft_id}.json"
    draft_path.write_text(json.dumps(draft_data, indent=2))

    print(f"\n{'─'*50}", flush=True)
    print(f"  DRAFT READY — ID: {draft_id}", flush=True)
    print(f"{'─'*50}", flush=True)
    print(f"\n  SCRIPT:\n  {draft_data['script']}\n", flush=True)
    print(f"  B-ROLL PROMPTS:", flush=True)
    for i, p in enumerate(draft_data["broll_prompts"], 1):
        print(f"  {i}. {p[:100]}...", flush=True)
    print(f"\n  TITLE: {draft_data['title']}", flush=True)
    print(f"  CAPTION: {draft_data['caption']}", flush=True)
    print(f"{'─'*50}", flush=True)
    print(f"  Draft saved: {draft_path}", flush=True)
    print(f"  To produce: python3 pipeline.py produce --id {draft_id}", flush=True)
    print(f"  ⏱  Done in {time.time()-t0:.1f}s", flush=True)
    print(f"{'═'*50}\n", flush=True)

    return draft_id, draft_path


def cmd_produce(draft_id: str):
    draft_path = DRAFTS_DIR / f"{draft_id}.json"
    if not draft_path.exists():
        raise FileNotFoundError(f"Draft not found: {draft_path}")

    draft = json.loads(draft_path.read_text())
    t0 = time.time()

    print(f"\n{'═'*50}", flush=True)
    print(f"  YouTube Shorts Pipeline — Produce", flush=True)
    print(f"  Draft: {draft_id}", flush=True)
    print(f"{'═'*50}", flush=True)

    work_dir = WORK_DIR / draft_id
    work_dir.mkdir(parents=True, exist_ok=True)

    voiceover, word_timings = generate_voiceover(draft["script"], work_dir)
    broll_clips = generate_broll(draft["broll_prompts"], work_dir)
    final_video = assemble_video(broll_clips, voiceover, work_dir)

    # Move to drafts dir
    output_path = DRAFTS_DIR / f"{draft_id}_final.mp4"
    import shutil
    shutil.copy2(final_video, output_path)

    draft["status"] = "produced"
    draft["video_path"] = str(output_path)
    draft_path.write_text(json.dumps(draft, indent=2))

    print(f"\n{'═'*50}", flush=True)
    print(f"  Video ready: {output_path}", flush=True)
    print(f"  To upload: python3 pipeline.py upload --id {draft_id}", flush=True)
    print(f"  ⏱  Total: {time.time()-t0:.1f}s", flush=True)
    print(f"{'═'*50}\n", flush=True)

    return str(output_path)


def cmd_upload(draft_id: str):
    draft_path = DRAFTS_DIR / f"{draft_id}.json"
    if not draft_path.exists():
        raise FileNotFoundError(f"Draft not found: {draft_path}")

    draft = json.loads(draft_path.read_text())
    if draft.get("status") != "produced":
        raise RuntimeError(f"Draft status is '{draft.get('status')}' — run produce first")

    video_path = Path(draft["video_path"])
    url = upload_to_youtube(
        video_path,
        title=draft["title"],
        description=draft["description"],
        tags=["shorts", "youtube shorts", draft.get("topic", "")[:30]],
    )

    draft["status"] = "uploaded"
    draft["youtube_url"] = url
    draft_path.write_text(json.dumps(draft, indent=2))

    print(f"\n  YouTube URL: {url}", flush=True)
    return url


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="YouTube Shorts Pipeline — AI-native end-to-end video creation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("draft", help="Generate script + metadata for a topic")
    p.add_argument("--topic", required=True, help="Topic or headline for the Short")

    p = sub.add_parser("produce", help="Generate video from approved draft")
    p.add_argument("--id", required=True, help="Draft ID from draft command")

    p = sub.add_parser("upload", help="Upload produced video to YouTube")
    p.add_argument("--id", required=True, help="Draft ID from draft command")

    args = parser.parse_args()

    if args.cmd == "draft":
        cmd_draft(args.topic)
    elif args.cmd == "produce":
        cmd_produce(args.id)
    elif args.cmd == "upload":
        cmd_upload(args.id)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
