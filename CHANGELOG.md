# Changelog

All notable changes to openclaw-mac will be documented here.
Format: [Semantic Versioning](https://semver.org)

---

## [1.0.0] — 2026-05-15

### Added
- `install.sh` — single-command Mac setup for OpenClaw
  - Apple Silicon + Intel support, Rosetta auto-install
  - Hostname prompt, headless system config (sleep, SSH, auto-restart)
  - Homebrew + core tools (git, node@24, python3, gh, ffmpeg, imagemagick, poppler, mas)
  - Productivity tools (yt-dlp, streamlink, tmux, ripgrep, tailscale, sag, gifgrep, Amphetamine)
  - Remote-access casks (BetterDisplay, Parsec, Jump Desktop Connect)
  - Python venv at `~/.openclaw-venv` with common SDKs (openai, anthropic, google-api, reportlab, pillow, pdfplumber)
  - uv + nano-pdf
  - OpenClaw + Claude Code + firecrawl-cli + agent-browser + clawvault + genspark
  - Workspace scaffold at `~/.openclaw/workspace/`
  - Identity templates (SOUL.md, AGENTS.md, TOOLS.md) with `[PLACEHOLDER]` values
  - Learnings files at `~/.learnings/` (ERRORS, LEARNINGS, DECISIONS, REGRESSIONS)
  - OpenClaw daemon install (survives reboots)
- 13 public skills bundled in `skills/`
- `templates/` directory with neutral identity files
- `.gitignore` blocks secrets, tokens, keys

### Skills bundled (v1.0.0)
- ai-agent-kill-switch
- ai-agent-ops-briefing
- fcpxml-from-script
- indic-language-translator
- local-lipsync
- outreach-crm
- song-identifier
- suno-music-gen
- twitch-ai-chatbot
- twitch-stream-monitor
- weekly-cost-report
- whatsapp-voice-transcriber
- youtube-shorts-pipeline

---

<!-- Add new entries at the top in reverse chronological order -->
