# openclaw-mac

> One-command Mac setup for an [OpenClaw](https://openclaw.ai) AI agent — base tools, productivity stack, and 13 ready-to-use skills.

Inspired by [thoughtbot/laptop](https://github.com/thoughtbot/laptop). Installs a clean, reproducible foundation for running an OpenClaw agent on any Mac — no API keys, no identity, no secrets baked in. Safe to re-run on an existing machine (every install is idempotent).

---

## Quick Start

Open Terminal on a fresh Mac and run:

```bash
git clone https://github.com/rushindrasinha/openclaw-mac.git
cd openclaw-mac
bash install.sh
```

Takes ~10 minutes. You'll be prompted once for a hostname.

> The script can also be run via `curl | bash`, but cloning first is recommended so the skills folder is available locally for installation.

---

## What It Does (Step by Step)

`install.sh` runs in this order:

1. **Detects architecture** — Apple Silicon (M-series) or Intel. On Apple Silicon, installs Rosetta 2 automatically.
2. **Sets hostname** — prompts you to name the machine.
3. **Configures for headless operation** — disables sleep, enables SSH, disables screen saver, enables auto-restart after power failure.
4. **Installs Homebrew** — skips if already present.
5. **Installs core tools** via Homebrew — git, node, python3, wget, jq, gh, ffmpeg, imagemagick, poppler, mas.
6. **Installs productivity tools** — yt-dlp, streamlink, tmux, ripgrep, tailscale, sag (TTS), gifgrep.
7. **Installs remote-access casks** — BetterDisplay, Parsec, Jump Desktop Connect.
8. **Installs Amphetamine** via mas (Mac App Store) — keeps the Mac awake during remote sessions.
9. **Upgrades Node to v24** if current version is below 24 (required for OpenClaw).
10. **Creates a Python venv** at `~/.openclaw-venv` and installs packages.
11. **Installs uv** — fast Python runner, used by some agent scripts.
12. **Installs OpenClaw** via npm (`npm install -g openclaw@latest`).
13. **Installs Claude Code** via npm (`npm install -g @anthropic-ai/claude-code`).
14. **Installs npm CLI tools** — firecrawl-cli, agent-browser, clawvault, @genspark/cli.
15. **Scaffolds workspace** at `~/.openclaw/workspace/` — creates `memory/`, `.agents/skills/`, and `~/.learnings/`.
16. **Installs identity templates** — `SOUL.md`, `AGENTS.md`, `TOOLS.md` (with `[PLACEHOLDER]` values for you to fill in).
17. **Installs 13 public skills** into `~/.openclaw/workspace/.agents/skills/`.
18. **Creates learnings files** — blank `ERRORS.md`, `LEARNINGS.md`, `DECISIONS.md`, `REGRESSIONS.md` in `~/.learnings/`.
19. **Authenticates GitHub** (optional) via `gh auth login --web`.
20. **Installs OpenClaw as a daemon** — survives reboots via launchd.

---

## What It Installs

### Core tools

| Tool | Purpose |
|------|---------|
| Homebrew | Mac package manager |
| Node 24 | Runtime for OpenClaw |
| Python 3 + venv | Scripting + automation |
| OpenClaw | AI agent platform |
| Claude Code | Agentic coding CLI (`claude` command) |
| uv | Fast Python package runner |
| git | Version control |
| jq | JSON parsing in shell scripts |
| wget | HTTP downloads |
| gh | GitHub CLI |
| ffmpeg | Video/audio processing |
| imagemagick | Image manipulation |
| poppler | PDF utilities |
| mas | Mac App Store CLI |

### Productivity tools

| Tool | Purpose |
|------|---------|
| yt-dlp | YouTube/Twitch video downloader |
| streamlink | Stream recording (Twitch, YouTube Live) |
| tmux | Terminal session manager (persists across SSH disconnects) |
| ripgrep | Fast file search |
| tailscale | Private VPN mesh (cross-machine communication) |
| sag | ElevenLabs TTS CLI |
| gifgrep | Search inside GIFs |
| nano-pdf | PDF generation (uv tool) |
| Amphetamine | Keeps Mac awake during remote sessions |

### Remote-access casks

| App | Purpose |
|-----|---------|
| BetterDisplay | Virtual display for headless operation |
| Parsec | Low-latency remote desktop |
| Jump Desktop Connect | iPad → Mac remote access |

### npm packages

| Package | Purpose |
|---------|---------|
| openclaw | The agent runtime |
| @anthropic-ai/claude-code | Agentic coding CLI |
| firecrawl-cli | Web scraping CLI |
| agent-browser | Headless browser for agents |
| clawvault | Credential vault for OpenClaw |
| @genspark/cli | Genspark AI CLI |

### Python packages (installed into `~/.openclaw-venv`)

| Package | Purpose |
|---------|---------|
| requests | HTTP client |
| python-dotenv | `.env` file loading |
| openai | OpenAI SDK |
| anthropic | Anthropic SDK |
| reportlab | PDF generation |
| pillow | Image processing |
| pdfplumber | PDF text extraction |
| google-auth | Google OAuth2 |
| google-auth-oauthlib | Google OAuth2 flow |
| google-api-python-client | Google APIs (Drive, Sheets, etc.) |

---

## Skills Installed (13)

All skills are copied into `~/.openclaw/workspace/.agents/skills/` and become available to your agent automatically.

| Skill | Trigger phrases | What it does |
|-------|-----------------|--------------|
| `ai-agent-kill-switch` | "kill switch", "emergency stop", "pause all automation" | Phrase-triggered emergency halt. Stops all agent automation instantly via a LaunchAgent watchdog that survives reboots. |
| `ai-agent-ops-briefing` | "daily brief", "ops briefing", "MRR status", "who's overdue?" | Produces a daily ops brief from a customers directory: MRR, credit balances, overdue payments, churn risk flags. |
| `fcpxml-from-script` | "create Final Cut project", "FCPXML from script" | Takes a script file + audio file → generates a valid FCPXML project file ready to open in Final Cut Pro. |
| `indic-language-translator` | "translate to Hindi", "convert to Marathi" | Translates to/from any Indian language (Hindi, Tamil, Telugu, Bengali, Marathi, Kannada, Malayalam, Gujarati, Punjabi, Urdu, Odia, Assamese, Sanskrit) and global languages. |
| `local-lipsync` | "local lipsync", "sync audio to video", "Wav2Lip" | On-device lipsync using Wav2Lip. Runs fully locally — no cloud, no cost. Includes Apple Silicon patches. |
| `outreach-crm` | "add this lead", "mark as replied", "show pipeline" | Lightweight JSON-backed sales CRM. Track leads through stages: sent → replied → booked → closed → dead. |
| `song-identifier` | "what is this song?", "shazam this" | Takes any audio file → returns song title, artist, album, release date, Spotify link, Apple Music link. |
| `suno-music-gen` | "generate AI music", "create a song", "instrumental track" | Generates music via Suno — instrumentals, full songs with lyrics, genre-specific tracks. |
| `twitch-ai-chatbot` | "deploy Twitch chatbot", "set up Twitch bot" | AI-powered chatbot for any Twitch channel. Responds to a configurable trigger word. Pure WebSocket IRC. |
| `twitch-stream-monitor` | "monitor Twitch", "record stream when live" | Monitors Twitch channels. Starts recording with streamlink when live, uploads to Google Drive, sends notifications. |
| `weekly-cost-report` | "cost report", "model usage summary", "API costs" | Parses OpenClaw JSONL session logs. Outputs per-model token counts + dollar costs for the last 7 days. |
| `whatsapp-voice-transcriber` | "transcribe this voice note" | Transcribes OGG/MP3/WAV audio using Whisper. Classifies output as Idea/Task, Draft, or Note. |
| `youtube-shorts-pipeline` | "create YouTube Short", "Shorts pipeline" | End-to-end pipeline: topic or headline → script → voiceover (via TTS) → upload-ready video file. |

Each skill is a folder with a `SKILL.md` manifest. OpenClaw reads these at session start and invokes the skill when a user message matches its trigger phrases.

---

## What It Configures

### Headless operation (all settings are system-level)

| Setting | Command | Why |
|---------|---------|-----|
| Hostname | `scutil --set ComputerName/HostName/LocalHostName` | Identify the machine on the network |
| Display sleep | `pmset -a displaysleep 0` | Don't go dark mid-session |
| System sleep | `pmset -a sleep 0` | Stay on between connections |
| Disk sleep | `pmset -a disksleep 0` | Stay accessible during heavy I/O |
| SSH / Remote Login | `systemsetup -setremotelogin on` | SSH access from anywhere |
| Screen saver | `defaults write idleTime 0` | No interruptions |
| Auto-restart | `pmset -a autorestart 1` | Comes back after power outage |

### PATH additions (written to `~/.zshrc`)

- Homebrew shellenv
- `node@24` bin path (if upgraded)
- `~/.openclaw-venv/bin` (Python venv)
- `~/.local/bin` (uv)

---

## After Install

```bash
# Step 1 — Reload shell
source ~/.zshrc

# Step 2 — Edit your identity files
nano ~/.openclaw/workspace/SOUL.md    # AI personality + operating rules
nano ~/.openclaw/workspace/AGENTS.md  # Session behavior, memory rules, red lines
nano ~/.openclaw/workspace/TOOLS.md   # Environment notes (SSH, devices, TTS)

# Step 3 — Connect API keys
openclaw auth login

# Step 4 — Link a messaging channel (WhatsApp, Telegram, etc.)
openclaw channels login

# Step 5 — Verify the daemon is running
openclaw gateway status

# Step 6 — Send /status on your linked channel
# The agent should respond.
```

---

## Workspace Layout

After install, your workspace looks like this:

```
~/.openclaw/workspace/
  SOUL.md              ← AI personality, values, operating rules
  AGENTS.md            ← Session startup, memory rules, red lines
  TOOLS.md             ← Environment-specific notes
  memory/              ← Agent memory files (created by agent over time)
  .agents/skills/      ← 13 installed skills

~/.learnings/
  ERRORS.md            ← Raw incidents: what went wrong + root cause
  LEARNINGS.md         ← Validated patterns promoted from ERRORS
  DECISIONS.md         ← Deliberate architectural/behavioral choices
  REGRESSIONS.md       ← Things that broke after working correctly
```

The three identity files (`SOUL.md`, `AGENTS.md`, `TOOLS.md`) are injected into every agent session at startup. They are your agent's memory across reboots.

---

## The Identity Files

### SOUL.md — Who the agent is

Personality, values, operating rules, tone, and red lines. The agent reads this at the start of every session.

Key things to fill in after install:
- `[AI_NAME]` — what to call the agent (e.g. Ares, Nova, Hermes, anything you like)
- `[OWNER_NAME]` — your name
- `[TIMEZONE]` — e.g. `Asia/Kolkata`, `America/New_York`
- Any domain-specific rules, communication style preferences, or off-limits behaviors

### AGENTS.md — How the agent behaves

Session startup sequence, memory read/write rules, how the agent handles uncertainty, what it must never do. More operational than `SOUL.md`.

### TOOLS.md — What's on this machine

SSH host aliases, camera/microphone device names, TTS voice preferences, API endpoint nicknames, local tool paths. Specific to the hardware this instance is running on.

---

## Architecture Notes

- **Apple Silicon (M1/M2/M3/M4+):** Homebrew installs to `/opt/homebrew`. Rosetta 2 is installed automatically.
- **Intel:** Homebrew installs to `/usr/local`. No Rosetta needed.
- The script detects arch via `uname -m` and sets `HOMEBREW_PREFIX` accordingly.
- All installs check if the tool is already present before installing — safe to re-run.

---

## Security Notes

- **No secrets are injected** — zero API keys, tokens, or credentials are written to disk by `install.sh`.
- API keys are added later via `openclaw auth login` per provider.
- The `.gitignore` in this repo blocks `*.env`, `*.pem`, `*.key`, and other credential file patterns from being committed.
- GitHub auth (`gh auth login`) is done via browser OAuth — no credentials are stored in plaintext.

---

## Troubleshooting

**Homebrew install hangs:** Check your internet connection. Homebrew installation can take 1–2 minutes.

**`openclaw: command not found` after install:** Run `source ~/.zshrc` to reload PATH. If still missing, check that `npm install -g openclaw` succeeded (scroll up in the install output).

**GitHub auth fails:** Run `gh auth login --web` manually after install. (GitHub auth is optional — only needed if you'll be cloning private repos.)

**`mas` can't install Amphetamine:** You need to be signed into the Mac App Store before running the script. If it fails, install [Amphetamine](https://apps.apple.com/app/id937984704) manually.

**Node version still old after upgrade:** Run `source ~/.zshrc` and check `node --version`. If still wrong, check if another node manager (nvm, volta) is overriding the PATH.

**Skills not loading:** Verify they were copied: `ls ~/.openclaw/workspace/.agents/skills/`. If empty, you ran the script via `curl | bash` without the local skills folder — clone the repo and run `bash install.sh` from inside it.

**OpenClaw daemon not running:** Run `openclaw onboard --install-daemon` manually. Check status with `openclaw gateway status`.

---

## Adding Your Own Skills

Each skill is a folder with at least a `SKILL.md` file:

```
skills/
  my-custom-skill/
    SKILL.md          ← skill manifest (name, description, trigger phrases)
    scripts/
      run.py          ← implementation (optional)
```

To install: drop the folder into `~/.openclaw/workspace/.agents/skills/` and restart the gateway:

```bash
openclaw gateway restart
```

Or re-run `bash install.sh` (it will copy any new skills from this repo's `skills/` directory).

---

## Customizing for a New Machine

1. Fork or clone this repo
2. Add your own skills to `skills/`
3. Edit `templates/SOUL.md`, `AGENTS.md`, `TOOLS.md` with your defaults
4. Run `bash install.sh` on the new Mac

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## License

MIT
