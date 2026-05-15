---
name: indic-language-translator
description: Use when a user wants to translate text to or from any Indian language — Hindi, Tamil, Telugu, Bengali, Marathi, Kannada, Malayalam, Gujarati, Punjabi, Urdu, Odia, Assamese, Sanskrit — or says "translate this message", "translate this to Hindi", "what does this say in Tamil", "convert to Marathi", or similar. Also handles global languages (Spanish, French, Arabic, Chinese, Japanese, Korean, etc.). Uses Gemini 2.5 Flash. Also use when asked to detect what language a piece of text is written in.
---

# Indic Language Translator

## Overview
High-quality translation to/from Indian and global languages using Gemini 2.5 Flash. Supports 13 Indian languages and 10 global languages. Also detects language from input text.

## Usage

Translate text:
```
python3 scripts/translate.py "Your order is confirmed" --to hi
python3 scripts/translate.py "आपका ऑर्डर कन्फर्म हो गया" --to en
python3 scripts/translate.py "Hello" --to ta --from en
```

Detect language:
```
python3 scripts/translate.py "नमस्ते" --detect
```

List supported languages:
```
python3 scripts/translate.py --list
```

JSON output:
```
python3 scripts/translate.py "Hello" --to hi --json
```

Pipe stdin:
```
echo "Hello world" | python3 scripts/translate.py --to mr
```

## Workflow
1. Receive text and target language from user request
2. Map language name to ISO code if needed (e.g. "Hindi" → `hi`, "Tamil" → `ta`)
3. Run `scripts/translate.py "<text>" --to <code>`
4. Script calls Gemini 2.5 Flash with zero temperature (deterministic output)
5. Returns only the translated text — no labels, quotes, or explanations
6. For batch translation, use `translate_batch()` as a module to translate multiple strings in one API call

## Supported Language Codes
Indian: `hi` Hindi, `ta` Tamil, `te` Telugu, `mr` Marathi, `bn` Bengali, `gu` Gujarati, `kn` Kannada, `ml` Malayalam, `pa` Punjabi, `ur` Urdu, `or` Odia, `as` Assamese, `sa` Sanskrit

Global: `en` English, `es` Spanish, `fr` French, `de` German, `pt` Portuguese, `ar` Arabic, `zh` Chinese, `ja` Japanese, `ko` Korean, `ru` Russian, `id` Indonesian

## Scripts
- `scripts/translate.py` — CLI and importable module. Functions: `translate(text, to_lang, from_lang)`, `detect_language(text)`, `translate_batch(texts, to_lang)`. Uses Gemini API directly via `urllib` (no extra dependencies).

## Requirements
- Gemini API key (embedded; also reads `GEMINI_API_KEY` or `GOOGLE_API_KEY` env vars)
- Python 3.10+ (uses `list[str]` type hints)
- Internet connection
