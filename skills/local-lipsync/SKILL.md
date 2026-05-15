# local-lipsync

**Trigger:** local lipsync, sync audio to video, Wav2Lip, Apple Silicon lipsync, free lipsync, lipsync video, make lips match audio

## What This Does

Lip-syncs audio to a face/portrait video using local Wav2Lip + GFPGAN enhancement. Free, runs offline, Apple Silicon compatible.

## Three-Tier Lipsync Strategy

Choose tier based on quality needed and budget:

| Tier | Tool | Cost | Use For |
|------|------|------|---------|
| **1 — Local** | Wav2Lip + GFPGAN | Free | Drafts, testing, iteration |
| **2 — Cloud** | LatentSync on Replicate | ~$0.10/clip | Final content, better quality |
| **3 — Hero** | OmniHuman | Highest | Hero content, launch videos only |

**Decision rule:** draft = local → final = Replicate → hero = OmniHuman

---

## Tier 1: Local Wav2Lip (Free)

### Quick Run

```bash
bash ~/.openclaw/workspace/.agents/skills/local-lipsync/scripts/run_lipsync.sh \
    --input-video /path/to/face.mp4 \
    --audio /path/to/audio.wav \
    --output ~/output_lipsynced.mp4
```

Default output if `--output` omitted: `~/wav2lip_enhanced.mp4`

The existing pipeline script at `~/wav2lip/run_pipeline.sh` also works:
```bash
bash ~/wav2lip/run_pipeline.sh <face_video> <audio_wav> <output_mp4>
```

### Requirements

- `~/wav2lip/` — Wav2Lip repo cloned
- `~/wav2lip/checkpoints/wav2lip_gan.pth` — model weights
- `~/wav2lip/enhance.py` — GFPGAN integration (see references/apple-silicon-patches.md)
- conda env `latentsync` active
- ffmpeg installed

### Setup (if not already done)

```bash
# Clone Wav2Lip
git clone https://github.com/Rudrabha/Wav2Lip.git ~/wav2lip

# Download model weights
mkdir -p ~/wav2lip/checkpoints
# wav2lip_gan.pth from: https://github.com/Rudrabha/Wav2Lip/tree/master#getting-the-checkpoints

# Install deps in latentsync env
conda run -n latentsync pip install librosa scipy face-alignment gfpgan basicsr facexlib

# Download GFPGAN model
mkdir -p ~/wav2lip/gfpgan/weights
curl -L "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth" \
    -o ~/wav2lip/gfpgan/weights/GFPGANv1.4.pth
```

### Apple Silicon Fixes

See `references/apple-silicon-patches.md` for exact code patches:
- **audio.py** — replace soundfile with librosa
- **inference.py** — replace s3fd with RetinaFace
- **enhance.py** — full GFPGAN v1.4 integration script

---

## Tier 2: LatentSync on Replicate (~$0.10/clip)

Better quality, especially for talking-head videos.

```python
import replicate

output = replicate.run(
    "bytedance/latentsync:latest",
    input={
        "video": open("/path/to/face.mp4", "rb"),
        "audio": open("/path/to/audio.wav", "rb"),
    }
)
print(output)  # URL to result
```

Or via CLI:
```bash
replicate run bytedance/latentsync \
    --input video=@face.mp4 \
    --input audio=@audio.wav
```

Requires: `REPLICATE_API_TOKEN` set in environment.

---

## Tier 3: OmniHuman (Hero only)

Highest quality photorealistic lipsync. Reserve for launch videos, hero content, and showcase clips. Not automated — access via web interface or API if available.

---

## Tips

- Input video: clear frontal face, good lighting, 720p+
- Audio: clean, no music/background noise (use separated voice track)
- Pad arg `--pads 0 15 0 0` shifts the mouth region up — adjust if lips are misaligned
- For music videos: separate vocals first with `demucs` before passing to lipsync

## Files

- `scripts/run_lipsync.sh` — main wrapper script
- `references/apple-silicon-patches.md` — code patches for Apple Silicon compatibility
