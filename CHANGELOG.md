# Changelog

All notable changes to openclaw-mac will be documented here.
Format: [Semantic Versioning](https://semver.org)

---

## [1.0.0] — 2026-05-15

### Added
- `install.sh` — minimal one-command Mac setup
  - Apple Silicon + Intel support, Rosetta auto-install
  - Homebrew + core tools (git, node@24, python3, gh)
  - OpenClaw + Claude Code via npm
  - Workspace scaffold at `~/.openclaw/workspace/`
  - Identity templates (SOUL.md, AGENTS.md, TOOLS.md) with `[PLACEHOLDER]` values
- `templates/` — neutral identity files
- `.gitignore` blocks secrets, tokens, keys
- Idempotent installs, safe to re-run

### Design notes
- No skills bundled — skills are opinionated; install them later from the OpenClaw registry
- No headless/remote tooling — that's a downstream concern, not a fresh-install need
- No media tooling (ffmpeg, yt-dlp, streamlink) — install only what your skills require

---

<!-- Add new entries at the top in reverse chronological order -->
