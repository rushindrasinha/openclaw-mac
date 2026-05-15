#!/bin/bash
#
# openclaw-mac — Minimal Mac setup for OpenClaw
# https://github.com/rushindrasinha/openclaw-mac
#
# Installs only what's needed to run OpenClaw on a fresh Mac:
#   Homebrew, Node 24, Python 3, git, gh, OpenClaw, Claude Code.
#   Scaffolds the workspace and drops in identity templates.
#
# Usage:
#   bash <(curl -fsSL https://raw.githubusercontent.com/rushindrasinha/openclaw-mac/main/install.sh)
#

set -e

REPO_RAW="https://raw.githubusercontent.com/rushindrasinha/openclaw-mac/main"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]:-$0}" )" 2>/dev/null && pwd )"

fancy_echo() { printf "\n\033[1;34m▶ %s\033[0m\n" "$*"; }
success_echo() { printf "\033[1;32m✓ %s\033[0m\n" "$*"; }
warn_echo() { printf "\033[1;33m⚠ %s\033[0m\n" "$*"; }

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
for pkg in git node python3 gh; do
  if brew list --formula "$pkg" &>/dev/null; then
    echo "  → $pkg already installed"
  else
    brew install "$pkg"
  fi
done
success_echo "Core tools installed"

# ── Node 24 (OpenClaw requirement) ────────────────────────────────────────────
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

# ── OpenClaw ──────────────────────────────────────────────────────────────────
fancy_echo "Installing OpenClaw..."
npm install -g openclaw@latest
success_echo "OpenClaw $(openclaw --version 2>/dev/null || echo 'installed')"

# ── Claude Code ───────────────────────────────────────────────────────────────
fancy_echo "Installing Claude Code..."
npm install -g @anthropic-ai/claude-code
success_echo "Claude Code $(claude --version 2>/dev/null || echo 'installed')"

# ── Workspace scaffold ────────────────────────────────────────────────────────
fancy_echo "Scaffolding workspace..."
WORKSPACE="${HOME}/.openclaw/workspace"
mkdir -p "$WORKSPACE/memory" "$WORKSPACE/.agents/skills"
success_echo "Workspace ready at $WORKSPACE"

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

# ── Done ──────────────────────────────────────────────────────────────────────
printf "\n"
printf "\033[1;32m╔════════════════════════════════════════════╗\033[0m\n"
printf "\033[1;32m║       OpenClaw Mac setup complete ✓        ║\033[0m\n"
printf "\033[1;32m╚════════════════════════════════════════════╝\033[0m\n"
printf "\n"
printf "Next steps:\n"
printf "  1. Reload shell                 →  source ~/.zshrc\n"
printf "  2. Edit your identity files     →  nano ~/.openclaw/workspace/SOUL.md\n"
printf "                                      nano ~/.openclaw/workspace/AGENTS.md\n"
printf "                                      nano ~/.openclaw/workspace/TOOLS.md\n"
printf "  3. Run onboarding               →  openclaw onboard --install-daemon\n"
printf "  4. Connect API keys             →  openclaw auth login\n"
printf "  5. Link a messaging channel     →  openclaw channels login\n"
printf "  6. Verify                       →  openclaw gateway status\n"
printf "\n"
printf "Docs:  https://docs.openclaw.ai\n"
printf "Repo:  https://github.com/rushindrasinha/openclaw-mac\n"
printf "\n"
