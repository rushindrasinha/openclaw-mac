#!/bin/bash
#
# openclaw-mac — One-command Mac setup for OpenClaw AI agent instances
# https://github.com/rushindrasinha/openclaw-mac
#
# Usage:
#   bash <(curl -fsSL https://raw.githubusercontent.com/rushindrasinha/openclaw-mac/main/install.sh)
#
# Or, if cloned locally:
#   bash install.sh
#

set -e

REPO_RAW="https://raw.githubusercontent.com/rushindrasinha/openclaw-mac/main"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]:-$0}" )" 2>/dev/null && pwd )"

fancy_echo() {
  printf "\n\033[1;34m▶ %s\033[0m\n" "$*"
}
success_echo() {
  printf "\033[1;32m✓ %s\033[0m\n" "$*"
}
warn_echo() {
  printf "\033[1;33m⚠ %s\033[0m\n" "$*"
}

# ── Detect arch ───────────────────────────────────────────────────────────────
arch="$(uname -m)"
if [ "$arch" = "arm64" ]; then
  HOMEBREW_PREFIX="/opt/homebrew"
  if ! pkgutil --pkg-info=com.apple.pkg.RosettaUpdateAuto > /dev/null 2>&1; then
    fancy_echo "Installing Rosetta 2..."
    softwareupdate --install-rosetta --agree-to-license
  fi
else
  HOMEBREW_PREFIX="/usr/local"
fi

# ── zshrc helper ──────────────────────────────────────────────────────────────
append_to_zshrc() {
  local text="$1"
  local zshrc="$HOME/.zshrc"
  [ ! -f "$zshrc" ] && touch "$zshrc"
  grep -qF "$text" "$zshrc" 2>/dev/null || printf "\n%s\n" "$text" >> "$zshrc"
}

# ── Hostname ──────────────────────────────────────────────────────────────────
fancy_echo "Set machine hostname"
printf "Enter hostname for this Mac (e.g. claw-mini, agent-host): "
read -r MACHINE_NAME
if [ -n "$MACHINE_NAME" ]; then
  sudo scutil --set ComputerName "$MACHINE_NAME"
  sudo scutil --set HostName "$MACHINE_NAME"
  sudo scutil --set LocalHostName "$MACHINE_NAME"
  success_echo "Hostname set to: $MACHINE_NAME"
else
  warn_echo "Skipped — hostname not changed"
fi

# ── System prefs (headless-safe) ──────────────────────────────────────────────
fancy_echo "Configuring system for headless operation..."
sudo pmset -a displaysleep 0 sleep 0 disksleep 0 2>/dev/null && success_echo "Sleep disabled"
sudo systemsetup -setremotelogin on 2>/dev/null && success_echo "SSH / Remote Login enabled"
defaults write com.apple.screensaver idleTime 0 2>/dev/null && success_echo "Screen saver disabled"
sudo pmset -a autorestart 1 2>/dev/null && success_echo "Auto-restart after power failure enabled"

# ── Homebrew ──────────────────────────────────────────────────────────────────
if ! command -v brew >/dev/null 2>&1; then
  fancy_echo "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  append_to_zshrc "eval \"\$(${HOMEBREW_PREFIX}/bin/brew shellenv)\""
  eval "$($HOMEBREW_PREFIX/bin/brew shellenv)"
else
  success_echo "Homebrew already installed"
fi

export PATH="$HOMEBREW_PREFIX/bin:$PATH"
brew update --quiet

# ── Core tools ────────────────────────────────────────────────────────────────
fancy_echo "Installing core tools..."
CORE_TOOLS=(git node python3 wget jq gh ffmpeg imagemagick poppler mas)
for pkg in "${CORE_TOOLS[@]}"; do
  if brew list --formula "$pkg" &>/dev/null; then
    echo "  → $pkg already installed"
  else
    brew install "$pkg"
  fi
done
success_echo "Core tools installed"

# ── Productivity tools ────────────────────────────────────────────────────────
fancy_echo "Installing productivity + agent tools..."
PROD_TOOLS=(yt-dlp streamlink tmux ripgrep tailscale sag gifgrep)
for pkg in "${PROD_TOOLS[@]}"; do
  if brew list --formula "$pkg" &>/dev/null; then
    echo "  → $pkg already installed"
  else
    brew install "$pkg" || warn_echo "$pkg install failed — skipping"
  fi
done
success_echo "Productivity tools installed"

# ── GUI casks (headless remote access) ────────────────────────────────────────
fancy_echo "Installing GUI / remote-access casks..."
CASKS=(betterdisplay parsec jump-desktop-connect)
for cask in "${CASKS[@]}"; do
  if brew list --cask "$cask" &>/dev/null; then
    echo "  → $cask already installed"
  else
    brew install --cask "$cask" || warn_echo "$cask install failed — skipping"
  fi
done
success_echo "Casks installed"

# ── Amphetamine ───────────────────────────────────────────────────────────────
fancy_echo "Installing Amphetamine from App Store..."
if mas list 2>/dev/null | grep -q "937984704"; then
  success_echo "Amphetamine already installed"
else
  mas install 937984704 && success_echo "Amphetamine installed" \
    || warn_echo "Amphetamine install failed — install manually: https://apps.apple.com/app/id937984704"
fi

# ── Node 24 ───────────────────────────────────────────────────────────────────
NODE_MAJOR=$(node --version 2>/dev/null | sed 's/v//' | cut -d. -f1)
if [ -n "$NODE_MAJOR" ] && [ "$NODE_MAJOR" -lt 24 ]; then
  fancy_echo "Upgrading Node to v24 (required for OpenClaw)..."
  if brew list --formula node@24 &>/dev/null; then
    echo "  → node@24 already installed"
  else
    brew install node@24
  fi
  brew link --overwrite --force node@24 2>/dev/null || true
  append_to_zshrc "export PATH=\"${HOMEBREW_PREFIX}/opt/node@24/bin:\$PATH\""
  export PATH="${HOMEBREW_PREFIX}/opt/node@24/bin:$PATH"
fi
success_echo "Node $(node --version)"

# ── Python venv ───────────────────────────────────────────────────────────────
fancy_echo "Installing Python packages..."
CLAW_VENV="$HOME/.openclaw-venv"
python3 -m venv "$CLAW_VENV"
"$CLAW_VENV/bin/pip" install --quiet --upgrade pip
"$CLAW_VENV/bin/pip" install --quiet \
  requests reportlab pillow python-dotenv pdfplumber \
  google-auth google-auth-oauthlib google-api-python-client \
  openai anthropic
append_to_zshrc "export PATH=\"\$HOME/.openclaw-venv/bin:\$PATH\""
export PATH="$CLAW_VENV/bin:$PATH"
success_echo "Python packages installed (venv: $CLAW_VENV)"

# ── uv ────────────────────────────────────────────────────────────────────────
if ! command -v uv >/dev/null 2>&1; then
  fancy_echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  append_to_zshrc "export PATH=\"\$HOME/.local/bin:\$PATH\""
  export PATH="$HOME/.local/bin:$PATH"
else
  success_echo "uv already installed"
fi

# nano-pdf via uv
uv tool install nano-pdf 2>/dev/null && success_echo "nano-pdf installed" || echo "  → nano-pdf already installed"

# ── OpenClaw ──────────────────────────────────────────────────────────────────
fancy_echo "Installing OpenClaw..."
npm install -g openclaw@latest
success_echo "OpenClaw $(openclaw --version 2>/dev/null || echo 'installed')"

# ── Claude Code ───────────────────────────────────────────────────────────────
fancy_echo "Installing Claude Code..."
npm install -g @anthropic-ai/claude-code
success_echo "Claude Code $(claude --version 2>/dev/null || echo 'installed')"

# ── npm extras ────────────────────────────────────────────────────────────────
fancy_echo "Installing npm CLI tools..."
NPM_EXTRAS=(firecrawl-cli agent-browser clawvault @genspark/cli)
for pkg in "${NPM_EXTRAS[@]}"; do
  npm install -g "$pkg" --quiet 2>/dev/null && echo "  → $pkg" || warn_echo "$pkg install failed"
done
success_echo "npm tools installed"

# ── Workspace scaffold ────────────────────────────────────────────────────────
fancy_echo "Scaffolding workspace..."
WORKSPACE="${HOME}/.openclaw/workspace"
mkdir -p \
  "$WORKSPACE/memory" \
  "$WORKSPACE/.agents/skills" \
  "$HOME/.learnings"

# ── Identity templates ────────────────────────────────────────────────────────
fancy_echo "Installing identity templates..."
for f in SOUL.md AGENTS.md TOOLS.md; do
  if [ -f "$WORKSPACE/$f" ]; then
    echo "  → $f already exists, skipping"
  elif [ -f "$SCRIPT_DIR/templates/$f" ]; then
    cp "$SCRIPT_DIR/templates/$f" "$WORKSPACE/$f"
    echo "  → $f (from local)"
  else
    curl -fsSL "${REPO_RAW}/templates/${f}" -o "$WORKSPACE/$f" \
      && echo "  → $f (from repo)" \
      || warn_echo "Could not fetch $f — add it manually"
  fi
done

# ── Skills ────────────────────────────────────────────────────────────────────
fancy_echo "Installing public skills..."
if [ -d "$SCRIPT_DIR/skills" ]; then
  for skill in "$SCRIPT_DIR/skills"/*/; do
    name=$(basename "$skill")
    cp -R "$skill" "$WORKSPACE/.agents/skills/"
    echo "  → $name"
  done
  success_echo "Skills installed to $WORKSPACE/.agents/skills/"
else
  warn_echo "skills/ directory not found — clone the repo locally to install skills"
fi

# ── Learnings files ───────────────────────────────────────────────────────────
for f in ERRORS LEARNINGS DECISIONS REGRESSIONS; do
  touch "$HOME/.learnings/${f}.md"
done

# ── GitHub auth (optional) ────────────────────────────────────────────────────
fancy_echo "Authenticating GitHub (optional but recommended)..."
if ! gh auth status &>/dev/null; then
  printf "Run 'gh auth login --web' now? [Y/n] "
  read -r GH_LOGIN
  if [ "${GH_LOGIN:-y}" != "n" ] && [ "${GH_LOGIN:-y}" != "N" ]; then
    gh auth login --web --git-protocol https || warn_echo "GitHub auth skipped"
  fi
else
  success_echo "GitHub already authenticated ($(gh api user --jq '.login' 2>/dev/null))"
fi

# ── OpenClaw daemon ───────────────────────────────────────────────────────────
fancy_echo "Installing OpenClaw daemon (survives reboots)..."
openclaw onboard --install-daemon 2>/dev/null && success_echo "Daemon installed" \
  || warn_echo "Daemon install failed — run 'openclaw onboard --install-daemon' manually after editing identity files"

# ── Done ──────────────────────────────────────────────────────────────────────
printf "\n"
printf "\033[1;32m╔════════════════════════════════════════════╗\033[0m\n"
printf "\033[1;32m║       OpenClaw Mac setup complete ✓        ║\033[0m\n"
printf "\033[1;32m╚════════════════════════════════════════════╝\033[0m\n"
printf "\n"
printf "Next steps:\n"
printf "  1. Restart terminal              →  source ~/.zshrc\n"
printf "  2. Edit your identity files      →  nano ~/.openclaw/workspace/SOUL.md\n"
printf "                                       nano ~/.openclaw/workspace/AGENTS.md\n"
printf "                                       nano ~/.openclaw/workspace/TOOLS.md\n"
printf "  3. Connect API keys              →  openclaw auth login\n"
printf "  4. Link your messaging channel   →  openclaw channels login\n"
printf "  5. Verify the agent is running   →  openclaw gateway status\n"
printf "  6. Send /status on your channel  →  agent should respond\n"
printf "\n"
printf "Docs: https://docs.openclaw.ai\n"
printf "Repo: https://github.com/rushindrasinha/openclaw-mac\n"
printf "\n"
