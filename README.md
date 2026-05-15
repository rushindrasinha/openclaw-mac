# openclaw-mac

> Minimal one-command Mac setup for [OpenClaw](https://openclaw.ai).

Installs only what's needed to get an OpenClaw AI agent running on a fresh Mac — Homebrew, Node, Python, OpenClaw, Claude Code, and identity templates. No skills, no opinions, no secrets. Safe to re-run.

---

## Quick Start

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/rushindrasinha/openclaw-mac/main/install.sh)
```

Takes ~3 minutes.

---

## What It Installs

| Tool | Purpose |
|------|---------|
| Homebrew | Mac package manager |
| Node 24 | Runtime for OpenClaw |
| Python 3 | Required by OpenClaw + most agent scripts |
| git | Version control |
| gh | GitHub CLI (for cloning skills later) |
| OpenClaw | The agent platform itself |
| Claude Code | Agentic coding CLI (`claude` command) |

That's it. On Apple Silicon, Rosetta 2 is installed automatically.

---

## What It Scaffolds

```
~/.openclaw/workspace/
  SOUL.md              ← AI personality, values, operating rules
  AGENTS.md            ← Session startup, memory rules, red lines
  TOOLS.md             ← Environment-specific notes
  memory/              ← Agent memory (created by agent over time)
  .agents/skills/      ← Where skills go later
```

The three identity files are injected into every agent session at startup. Edit them before you run onboarding.

---

## After Install

```bash
# 1. Reload shell
source ~/.zshrc

# 2. Edit your identity files — replace [AI_NAME], [OWNER_NAME], [TIMEZONE]
nano ~/.openclaw/workspace/SOUL.md
nano ~/.openclaw/workspace/AGENTS.md
nano ~/.openclaw/workspace/TOOLS.md

# 3. Run onboarding (installs daemon, walks through API key setup)
openclaw onboard --install-daemon

# 4. Link a messaging channel (WhatsApp, Telegram, etc.)
openclaw channels login

# 5. Verify
openclaw gateway status

# 6. Send /status on your linked channel — the agent should respond
```

---

## The Identity Files

### SOUL.md — Who the agent is
Personality, values, operating rules, tone, red lines. Replace `[AI_NAME]`, `[OWNER_NAME]`, `[TIMEZONE]`.

### AGENTS.md — How the agent behaves
Session startup sequence, memory rules, what it must never do. More operational than `SOUL.md`.

### TOOLS.md — What's on this machine
SSH host aliases, device nicknames, TTS preferences. Fill in as you configure the machine.

---

## Adding Skills Later

Skills are folders with a `SKILL.md` manifest. To add one:

```bash
cp -R my-skill/ ~/.openclaw/workspace/.agents/skills/
openclaw gateway restart
```

Browse the OpenClaw skill registry at [docs.openclaw.ai](https://docs.openclaw.ai) or install via `clawhub`.

---

## Security Notes

- No secrets are injected — zero API keys, tokens, or credentials are written to disk by `install.sh`.
- API keys are added later via `openclaw auth login` per provider.
- GitHub auth (when you run `gh auth login` later) is done via browser OAuth.

---

## Troubleshooting

**Homebrew install hangs:** Check your internet connection. Installation can take 1–2 minutes.

**`openclaw: command not found` after install:** Run `source ~/.zshrc` to reload PATH. If still missing, check that `npm install -g openclaw` succeeded.

**Node version still old after upgrade:** Run `source ~/.zshrc` and check `node --version`. If still wrong, check if another node manager (nvm, volta) is overriding the PATH.

---

## License

MIT
