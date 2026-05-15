---
name: twitch-ai-chatbot
description: Deploy an AI chatbot in a Twitch channel that responds to a configurable trigger word (e.g. !bot), engages viewers with AI replies, and requires no Twitch API key — uses pure WebSocket IRC.
---

## Overview

Connects to Twitch IRC via WebSocket and responds to a trigger word using an Anthropic model. No Twitch API key required for basic operation — only a bot account OAuth token.

**Requirements:** `python3`, `aiohttp`, `websockets`, Anthropic API key.

---

## Setup

### 1. Create a bot Twitch account

Use a separate Twitch account for the bot. Get a chat OAuth token:

1. Go to: `https://twitchapps.com/tmi/`
2. Authorize with your **bot account** (not your main)
3. Copy the `oauth:XXXXXXXXXX` token

### 2. Configure

```bash
cd ~/.openclaw/workspace/.agents/skills/twitch-ai-chatbot/scripts
cp config.example.json config.json
```

Edit `config.json`:

```json
{
  "channel": "yourchannelname",
  "trigger_word": "!bot",
  "bot_login": "your_bot_account",
  "oauth_token": "oauth:XXXXXXXXXX",
  "model": "claude-haiku-4-5",
  "anthropic_api_key": "sk-ant-XXXXXXXX",
  "system_prompt": "You are a helpful and fun AI chatbot in a Twitch chat. Keep responses short (under 150 chars), casual, and engaging. No offensive content.",
  "cooldown_seconds": 30,
  "max_messages_per_30s": 18,
  "log_file": "chatbot.log",
  "storage_dir": "./storage"
}
```

**Key fields:**
- `channel` — Twitch channel to join (lowercase)
- `trigger_word` — command viewers type to talk to the bot (e.g. `!bot`, `!ai`, `!ask`)
- `bot_login` — Twitch username of the bot account
- `oauth_token` — OAuth token from twitchapps.com/tmi (include the `oauth:` prefix)
- `model` — Anthropic model ID. Recommended: `claude-haiku-4-5` (fast + cheap)
- `system_prompt` — customize the bot's personality and rules
- `cooldown_seconds` — minimum seconds between bot responses (prevents spam)

### 3. Install dependencies

```bash
pip3 install aiohttp websockets
```

### 4. Run

```bash
python3 ~/.openclaw/workspace/.agents/skills/twitch-ai-chatbot/scripts/chatbot.py
```

Or with a custom config path:

```bash
python3 chatbot.py --config /path/to/config.json
```

---

## Environment Variable Overrides

All key config values can be set via env vars (take precedence over config.json):

```bash
export TWITCH_CHANNEL=yourchannelname
export TWITCH_LOGIN=your_bot_account
export TWITCH_OAUTH=oauth:XXXXXXXXXX
export TRIGGER_WORD=!bot
export AI_MODEL=claude-haiku-4-5
export ANTHROPIC_API_KEY=sk-ant-XXXXXXXX
export SYSTEM_PROMPT="You are a helpful bot..."

python3 chatbot.py
```

---

## How It Works

1. Bot connects to `wss://irc-ws.chat.twitch.tv:443` — no API key needed
2. Joins configured channel
3. Watches all chat messages
4. When a message starts with `trigger_word`: calls Anthropic API with last 10 chat messages as context
5. Replies in chat: `@username <AI response>`
6. Rate limiting: max 18 msgs/30s, configurable cooldown between responses
7. Prompt injection sanitization built in
8. Chat history persisted to JSONL at `storage/chat_history.jsonl`

---

## Customizing the Bot

### Change trigger word

Update `trigger_word` in config.json. Examples: `!ai`, `!ask`, `!gpt`, `!help`

### Change personality

Update `system_prompt`. Example for a gaming bot:
```
You are an expert VALORANT coach in Twitch chat. Give quick tips and hype up plays. Max 150 chars per reply.
```

### Change model

- Fast/cheap: `claude-haiku-4-5`
- Smarter: `claude-sonnet-4-5`
- Avoid models with thinking tokens (slow, unpredictable output length)

---

## Running as a Background Service

### tmux

```bash
tmux new-session -d -s twitch-bot 'python3 ~/.openclaw/workspace/.agents/skills/twitch-ai-chatbot/scripts/chatbot.py'
```

### launchd (macOS)

Create `~/Library/LaunchAgents/com.twitch-ai-chatbot.plist` with appropriate configuration and `launchctl load` it.

---

## Troubleshooting

**Bot connects but doesn't respond:** Check trigger_word matches exactly. Verify bot account is in the channel (it joins automatically on connect).

**Authentication failed:** Regenerate OAuth token at twitchapps.com/tmi. Tokens expire.

**Rate limited by Twitch:** Increase `cooldown_seconds`. Default 30s is safe for most use.

**AI replies are too long:** Add "Max 150 characters" to your `system_prompt`.
