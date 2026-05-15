#!/bin/bash
# run_lipsync.sh — Wav2Lip + GFPGAN lipsync pipeline (Apple Silicon compatible)
# Usage: run_lipsync.sh --input-video <path> --audio <path> [--output <path>]
#
# Runs Wav2Lip inference.py then GFPGAN enhance.py.
# Default output: ~/wav2lip_enhanced.mp4

set -e

INPUT_VIDEO=""
AUDIO=""
OUTPUT="$HOME/wav2lip_enhanced.mp4"
WAV2LIP_DIR="$HOME/wav2lip"
TEMP_RAW="/tmp/wav2lip_raw_$$.mp4"

usage() {
    echo "Usage: $0 --input-video <path> --audio <path> [--output <path>]"
    echo ""
    echo "Options:"
    echo "  --input-video   Path to face/portrait video (mp4, mov)"
    echo "  --audio         Path to audio file (wav, mp3)"
    echo "  --output        Output path (default: ~/wav2lip_enhanced.mp4)"
    exit 1
}

# Parse named args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --input-video) INPUT_VIDEO="$2"; shift 2 ;;
        --audio)       AUDIO="$2";       shift 2 ;;
        --output)      OUTPUT="$2";      shift 2 ;;
        --help|-h)     usage ;;
        *) echo "Unknown argument: $1"; usage ;;
    esac
done

# Validate
if [ -z "$INPUT_VIDEO" ] || [ -z "$AUDIO" ]; then
    echo "ERROR: --input-video and --audio are required."
    usage
fi

if [ ! -f "$INPUT_VIDEO" ]; then
    echo "ERROR: Input video not found: $INPUT_VIDEO"
    exit 1
fi

if [ ! -f "$AUDIO" ]; then
    echo "ERROR: Audio file not found: $AUDIO"
    exit 1
fi

if [ ! -d "$WAV2LIP_DIR" ]; then
    echo "ERROR: Wav2Lip not found at $WAV2LIP_DIR"
    echo "Clone it: git clone https://github.com/Rudrabha/Wav2Lip.git ~/wav2lip"
    exit 1
fi

echo "================================================"
echo " Wav2Lip + GFPGAN Lipsync Pipeline"
echo " Input:  $INPUT_VIDEO"
echo " Audio:  $AUDIO"
echo " Output: $OUTPUT"
echo "================================================"

# Step 1: Wav2Lip inference
echo ""
echo "Step 1/2: Running Wav2Lip inference..."
conda run -n latentsync bash -c "cd '$WAV2LIP_DIR' && python inference.py \
    --checkpoint_path checkpoints/wav2lip_gan.pth \
    --face '$INPUT_VIDEO' \
    --audio '$AUDIO' \
    --outfile '$TEMP_RAW' \
    --pads 0 15 0 0"

echo "Wav2Lip complete. Raw output: $TEMP_RAW"

# Step 2: GFPGAN enhancement
echo ""
echo "Step 2/2: Running GFPGAN enhancement..."
conda run -n latentsync bash -c "cd '$WAV2LIP_DIR' && python enhance.py \
    --input '$TEMP_RAW' \
    --output '$OUTPUT'"

# Cleanup
rm -f "$TEMP_RAW"

echo ""
echo "================================================"
echo " Done! Enhanced output: $OUTPUT"
echo "================================================"
