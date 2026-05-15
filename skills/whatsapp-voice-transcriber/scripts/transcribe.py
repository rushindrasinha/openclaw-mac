#!/usr/bin/env python3
"""Process a single voice note OGG file: transcribe + classify + send to WhatsApp"""
import sys, subprocess, os, json
from pathlib import Path

def transcribe(filepath):
    """Use whisper CLI to transcribe the audio file."""
    result = subprocess.run(
        ["/opt/homebrew/bin/whisper", str(filepath), "--model", "base", "--output_format", "txt", "--output_dir", "/tmp/"],
        capture_output=True, text=True, timeout=120
    )
    # Find output file
    stem = Path(filepath).stem
    txt_file = Path(f"/tmp/{stem}.txt")
    if txt_file.exists():
        return txt_file.read_text().strip()
    # Fallback: check whisper stdout
    if result.stdout:
        return result.stdout.strip()
    return None

def send_wa(message):
    """Send a WhatsApp message to the configured target ($WA_TARGET)."""
    target = os.environ.get("WA_TARGET", "")
    if not target:
        print(message)
        return
    subprocess.run([
        "/opt/homebrew/bin/openclaw", "message", "send",
        "--target", target,
        "--channel", "whatsapp",
        "--message", message
    ])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: voice_note_processor.py <file.ogg>")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"Processing: {filepath}")

    transcript = transcribe(filepath)

    if not transcript:
        print(f"Transcription failed for: {filepath}")
        send_wa(f"🎙️ *Voice Note* (transcription failed)\nFile: {Path(filepath).name}")
        sys.exit(1)

    # Simple classification heuristics
    lower = transcript.lower()
    if any(w in lower for w in ["remind", "todo", "task", "need to", "should", "must", "idea", "build", "make"]):
        prefix = "💡 *Idea / Task*"
    elif any(w in lower for w in ["tell", "message", "send", "write", "reply", "say"]):
        prefix = "✉️ *Draft*"
    else:
        prefix = "📝 *Note*"

    msg = f"{prefix}\n\n{transcript}\n\n_Transcribed from voice note_"
    send_wa(msg)
    print(f"Sent: {msg[:100]}...")
