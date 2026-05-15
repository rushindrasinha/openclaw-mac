# Apple Silicon Patches for Wav2Lip

Wav2Lip was built for Linux/x86. These patches make it run on Apple Silicon (M1/M2/M3/M4).

## Patch 1: audio.py — Replace soundfile with librosa

**Problem:** `soundfile` can fail to load/write certain audio on Apple Silicon due to libsndfile linkage issues.

**File:** `~/wav2lip/audio.py`

**Find:**
```python
import soundfile as sf
```

**Replace with:**
```python
import librosa
import soundfile as sf  # keep for writing; install with: pip install soundfile librosa
```

**OR if soundfile is fully broken, replace all sf.read/sf.write usage:**

```python
# Reading audio
# OLD: wav, sr = sf.read(wav_file)
# NEW:
wav, sr = librosa.load(wav_file, sr=None, mono=False)
if wav.ndim > 1:
    wav = wav.T  # librosa returns (channels, samples); soundfile returns (samples, channels)

# Writing audio  
# OLD: sf.write(path, wav, sr)
# NEW:
import scipy.io.wavfile as wavfile
wavfile.write(path, sr, (wav * 32767).astype('int16'))
```

**Install deps:**
```bash
conda run -n latentsync pip install librosa scipy
```

---

## Patch 2: inference.py — Replace s3fd with RetinaFace

**Problem:** s3fd face detector requires torch extensions that don't compile cleanly on Apple Silicon. RetinaFace works natively.

**File:** `~/wav2lip/inference.py`

**Find (near top, imports):**
```python
from face_detection import FaceAlignment, LandmarksType
```
or any reference to `face_detection` / `s3fd`.

**Replace with:**

```python
# Option A: Use face_alignment with retinaface backend
from face_alignment import FaceAlignment, LandmarksType

def get_smoothened_boxes(boxes, T):
    for i in range(len(boxes)):
        if i + T > len(boxes):
            window = boxes[len(boxes) - T:]
        else:
            window = boxes[i:i + T]
        boxes[i] = np.mean(window, axis=0)
    return boxes

def face_detect(images):
    detector = FaceAlignment(LandmarksType.TWO_D, flip_input=False, device='cpu')
    batch_size = args.face_det_batch_size
    while True:
        predictions = []
        try:
            for i in range(0, len(images), batch_size):
                predictions.extend(detector.get_landmarks_from_image(images[i]))
        except RuntimeError:
            if batch_size == 1:
                raise RuntimeError('image too small for face detection')
            batch_size //= 2
            print('Batch size reduced to {} for face detection'.format(batch_size))
            continue
        break
    # ... rest of face_detect function
```

**Option B: Use retinaface package (simpler):**
```python
from retinaface import RetinaFace

def face_detect(images):
    results = []
    for img in images:
        faces = RetinaFace.detect_faces(img)
        if not faces:
            raise ValueError("No face detected in frame")
        # Get first face bounding box
        face = list(faces.values())[0]
        x1, y1, x2, y2 = face['facial_area']
        results.append([[x1, y1, x2, y2]])
    return results
```

**Install deps:**
```bash
# Option A
conda run -n latentsync pip install face-alignment

# Option B
conda run -n latentsync pip install retina-face
```

---

## Patch 3: enhance.py — GFPGAN v1.4 Post-Processing Integration

**Problem:** Default Wav2Lip output is blurry/low-res around the mouth. GFPGAN v1.4 enhances faces in the output video.

**File:** `~/wav2lip/enhance.py` (may not exist — create it)

**Full enhance.py:**
```python
#!/usr/bin/env python3
"""GFPGAN v1.4 video enhancer for Wav2Lip output."""

import argparse
import cv2
import numpy as np
import os
import tempfile
from pathlib import Path

def enhance_video(input_path: str, output_path: str):
    """Enhance each frame using GFPGAN v1.4."""
    try:
        from gfpgan import GFPGANer
    except ImportError:
        raise ImportError("Install: pip install gfpgan basicsr facexlib")

    # Load model
    model_path = os.path.expanduser('~/wav2lip/gfpgan/weights/GFPGANv1.4.pth')
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"GFPGAN model not found at {model_path}\n"
            "Download: https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth"
        )

    restorer = GFPGANer(
        model_path=model_path,
        upscale=2,
        arch='clean',
        channel_multiplier=2,
        bg_upsampler=None,
    )

    # Open input video
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Enhancing {total} frames at {fps:.1f}fps ({w}x{h} → {w*2}x{h*2})...")

    # Temp output without audio
    tmp_video = tempfile.mktemp(suffix='.mp4')
    out = cv2.VideoWriter(tmp_video, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w*2, h*2))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % 25 == 0:
            print(f"  Frame {frame_idx}/{total}", end='\r', flush=True)

        # GFPGAN expects BGR
        _, _, enhanced = restorer.enhance(
            frame,
            has_aligned=False,
            only_center_face=False,
            paste_back=True,
        )
        out.write(enhanced)

    cap.release()
    out.release()
    print(f"\nEnhancement complete. Merging audio...")

    # Merge original audio with enhanced video
    os.system(
        f'ffmpeg -y -i "{tmp_video}" -i "{input_path}" '
        f'-c:v libx264 -crf 18 -preset slow '
        f'-c:a aac -map 0:v:0 -map 1:a:0 '
        f'"{output_path}" -loglevel error'
    )
    os.remove(tmp_video)
    print(f"Done: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GFPGAN enhancer for Wav2Lip output")
    parser.add_argument("--input", required=True, help="Input video path")
    parser.add_argument("--output", required=True, help="Output video path")
    args = parser.parse_args()
    enhance_video(args.input, args.output)
```

**Install GFPGAN:**
```bash
conda run -n latentsync pip install gfpgan basicsr facexlib

# Download model
mkdir -p ~/wav2lip/gfpgan/weights
curl -L "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth" \
    -o ~/wav2lip/gfpgan/weights/GFPGANv1.4.pth
```

---

## Quick Fix Summary

```bash
# All patches in one conda env
conda run -n latentsync pip install librosa scipy face-alignment gfpgan basicsr facexlib

# Or use retinaface instead of face-alignment
conda run -n latentsync pip install retina-face
```

## Known Working Config (Confirmed)

- macOS 14+ on M1/M2/M3
- conda env: `latentsync`
- Torch: via conda (MPS backend available but not required for Wav2Lip)
- Python 3.10+
- `~/wav2lip/run_pipeline.sh` is the canonical runner on this machine
