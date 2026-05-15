#!/usr/bin/env python3
"""
translate.py — Translation Wrapper
Uses Gemini 2.5 Flash for high-quality Indic language translation.

CLI:
    python3 translate.py "Your order is confirmed" --to hi
    python3 translate.py "Your order is confirmed" --to ta
    python3 translate.py "आपका ऑर्डर कन्फर्म हो गया" --detect

Module:
    from translate import translate, detect_language, LANGUAGES
    result = translate("Hello", to_lang="hi")
    lang = detect_language("नमस्ते")
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error

# ── Config ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "AIzaSyBCUTR_3Fpe-75tvOsvlw3L6i1bxpJpfmE"
GEMINI_MODEL   = "gemini-2.5-flash"
GEMINI_URL     = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

# ── Supported Languages ──────────────────────────────────────────────────────
LANGUAGES = {
    # Indian
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ur": "Urdu",
    "or": "Odia",
    "as": "Assamese",
    "sa": "Sanskrit",
    # Global
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "ar": "Arabic",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian",
    "id": "Indonesian",
}

def _gemini(prompt: str) -> str:
    """Send a prompt to Gemini 2.5 Flash and return the text response."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "thinkingConfig": {"thinkingBudget": 0}
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(GEMINI_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
            return body["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        raise RuntimeError(f"Gemini error: {err.get('error', {}).get('message', str(e))}")

def translate(text: str, to_lang: str, from_lang: str = "auto") -> str:
    """
    Translate text to the target language.
    
    Args:
        text:      Text to translate
        to_lang:   Target language code (e.g. "hi", "ta") or full name ("Hindi")
        from_lang: Source language code or "auto" for auto-detect
    
    Returns:
        Translated text string
    """
    if not text or not text.strip():
        return text

    # Resolve language name
    lang_name = LANGUAGES.get(to_lang.lower(), to_lang)

    if from_lang == "auto":
        prompt = (
            f"Translate the following text to {lang_name}. "
            f"Return ONLY the translated text, no explanations, no quotes, no labels.\n\n"
            f"{text}"
        )
    else:
        source_name = LANGUAGES.get(from_lang.lower(), from_lang)
        prompt = (
            f"Translate the following {source_name} text to {lang_name}. "
            f"Return ONLY the translated text, no explanations, no quotes, no labels.\n\n"
            f"{text}"
        )

    return _gemini(prompt)

def detect_language(text: str) -> dict:
    """
    Detect the language of input text.
    
    Returns:
        {"code": "hi", "name": "Hindi", "confidence": "high"}
    """
    prompt = (
        f"Detect the language of the following text. "
        f"Respond with JSON only: {{\"code\": \"<ISO 639-1 code>\", \"name\": \"<language name>\", \"confidence\": \"high|medium|low\"}}\n\n"
        f"{text}"
    )
    raw = _gemini(prompt)
    # Strip markdown code fences if present
    raw = raw.strip().strip("```json").strip("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"code": "unknown", "name": "Unknown", "confidence": "low", "raw": raw}

def translate_batch(texts: list[str], to_lang: str) -> list[str]:
    """
    Translate multiple strings in one API call (cheaper, faster).
    
    Args:
        texts:   List of strings to translate
        to_lang: Target language code
    
    Returns:
        List of translated strings in same order
    """
    if not texts:
        return []

    lang_name = LANGUAGES.get(to_lang.lower(), to_lang)
    numbered  = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))

    prompt = (
        f"Translate the following numbered items to {lang_name}. "
        f"Return ONLY the numbered translations in the same format, nothing else.\n\n"
        f"{numbered}"
    )
    raw = _gemini(prompt)

    # Parse numbered response
    results = []
    lines   = [l.strip() for l in raw.strip().split("\n") if l.strip()]
    for line in lines:
        # Remove leading "1. " "2. " etc
        if line and line[0].isdigit() and ". " in line:
            results.append(line.split(". ", 1)[1])
        elif line:
            results.append(line)

    # Pad or trim to match input length
    while len(results) < len(texts):
        results.append(texts[len(results)])  # fallback: original
    return results[:len(texts)]

# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Translate text using Gemini 2.5 Flash",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Supported language codes:\n  " + "\n  ".join(f"{k}: {v}" for k, v in LANGUAGES.items())
    )
    parser.add_argument("text",     nargs="?", help="Text to translate (or pipe via stdin)")
    parser.add_argument("--to",     "-t",      help="Target language code (e.g. hi, ta, mr)")
    parser.add_argument("--from",   "-f",      dest="from_lang", default="auto", help="Source language code (default: auto)")
    parser.add_argument("--detect", "-d",      action="store_true", help="Detect language instead of translating")
    parser.add_argument("--list",   "-l",      action="store_true", help="List supported languages")
    parser.add_argument("--json",   "-j",      action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.list:
        for code, name in LANGUAGES.items():
            print(f"  {code:4} {name}")
        return

    # Get text from arg or stdin
    text = args.text
    if not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            parser.print_help()
            sys.exit(1)

    if args.detect:
        result = detect_language(text)
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(f"Language: {result.get('name')} ({result.get('code')}) — Confidence: {result.get('confidence')}")
        return

    if not args.to:
        print("Error: --to <language_code> required for translation", file=sys.stderr)
        sys.exit(1)

    result = translate(text, to_lang=args.to, from_lang=args.from_lang)

    if args.json:
        print(json.dumps({
            "input":  text,
            "output": result,
            "to":     args.to,
            "from":   args.from_lang
        }, ensure_ascii=False))
    else:
        print(result)

if __name__ == "__main__":
    main()
