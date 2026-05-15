#!/usr/bin/env python3
"""
chatbot.py — Generic AI-powered Twitch chat bot.

Connects to Twitch IRC via WebSocket (no Twitch API key required for basic use).
Reads chat and responds to a configurable trigger word using an AI model.

Config: config.json (copy from config.example.json)
Env vars override config: TWITCH_CHANNEL, TWITCH_OAUTH, TWITCH_LOGIN,
                          TRIGGER_WORD, AI_MODEL, ANTHROPIC_API_KEY, SYSTEM_PROMPT

Usage:
    python3 chatbot.py [--config path/to/config.json]
"""

import asyncio
import json
import logging
import os
import re
import ssl
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

import websockets

# ── Config loading ────────────────────────────────────────────────────────────

def load_config(config_path: str = None) -> dict:
    """Load config from file, then override with env vars."""
    config = {}

    # Default config path
    if not config_path:
        config_path = Path(__file__).parent / "config.json"
    
    if Path(config_path).exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        print(f"WARNING: config.json not found at {config_path}. Using env vars only.")

    # Env var overrides (env takes precedence over config file)
    overrides = {
        "channel":          os.environ.get("TWITCH_CHANNEL"),
        "trigger_word":     os.environ.get("TRIGGER_WORD"),
        "bot_login":        os.environ.get("TWITCH_LOGIN"),
        "oauth_token":      os.environ.get("TWITCH_OAUTH"),
        "model":            os.environ.get("AI_MODEL"),
        "anthropic_api_key":os.environ.get("ANTHROPIC_API_KEY"),
        "system_prompt":    os.environ.get("SYSTEM_PROMPT"),
    }
    for key, val in overrides.items():
        if val:
            config[key] = val

    # Validate required fields
    required = ["channel", "bot_login", "oauth_token"]
    missing = [k for k in required if not config.get(k)]
    if missing:
        print(f"ERROR: Missing required config fields: {', '.join(missing)}")
        print("Copy config.example.json to config.json and fill in values.")
        sys.exit(1)

    # Defaults
    config.setdefault("trigger_word", "!bot")
    config.setdefault("model", "claude-haiku-4-5")
    config.setdefault("system_prompt", "You are a helpful and fun AI chatbot in a Twitch chat. Keep responses short (under 150 chars), casual, and engaging.")
    config.setdefault("cooldown_seconds", 30)
    config.setdefault("max_messages_per_30s", 18)
    config.setdefault("log_file", "chatbot.log")
    config.setdefault("storage_dir", str(Path(__file__).parent / "storage"))

    return config


# ── Logging setup ─────────────────────────────────────────────────────────────

def setup_logging(log_file: str):
    handlers = [logging.StreamHandler()]
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handlers.append(logging.FileHandler(log_path, mode="a"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )

logger = logging.getLogger("chatbot")

# ── Constants ─────────────────────────────────────────────────────────────────

TWITCH_IRC_URI = "wss://irc-ws.chat.twitch.tv:443"


# ── Bot ───────────────────────────────────────────────────────────────────────

class TwitchAIBot:
    def __init__(self, config: dict):
        self.config = config
        self.channel = config["channel"].lower()
        self.bot_login = config["bot_login"].lower()
        self.oauth_token = config["oauth_token"]
        self.trigger_word = config["trigger_word"].lower()
        self.model = config["model"]
        self.system_prompt = config["system_prompt"]
        self.cooldown_seconds = int(config["cooldown_seconds"])
        self.max_msgs_per_30s = int(config["max_messages_per_30s"])
        self.api_key = config.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")

        self.ws = None
        self.running = True
        self.msg_timestamps: list[float] = []
        self.last_response_time: float = 0
        self.chat_history: list[dict] = []
        self.max_history = 50

        # Storage
        storage_dir = Path(config["storage_dir"])
        storage_dir.mkdir(parents=True, exist_ok=True)
        self.chat_log_path = storage_dir / "chat_history.jsonl"

    async def connect(self):
        ssl_context = ssl.create_default_context()
        self.ws = await websockets.connect(TWITCH_IRC_URI, ssl=ssl_context)

        token = self.oauth_token
        if not token.startswith("oauth:"):
            token = f"oauth:{token}"

        await self.ws.send(f"PASS {token}")
        await self.ws.send(f"NICK {self.bot_login}")
        await self.ws.send("CAP REQ :twitch.tv/membership twitch.tv/tags twitch.tv/commands")
        await self.ws.send(f"JOIN #{self.channel}")

        logger.info(f"Connected to #{self.channel} as {self.bot_login}")

    async def send_message(self, text: str):
        """Send a message with rate limiting."""
        now = time.time()
        self.msg_timestamps = [t for t in self.msg_timestamps if now - t < 30]

        if len(self.msg_timestamps) >= self.max_msgs_per_30s:
            logger.warning("Rate limit hit — skipping message")
            return

        if not self.ws:
            return

        # Truncate to Twitch's 500-char limit
        text = text[:490]
        await self.ws.send(f"PRIVMSG #{self.channel} :{text}")
        self.msg_timestamps.append(now)
        self.last_response_time = now
        logger.info(f"Sent: {text}")

    def _sanitize(self, text: str) -> str:
        """Strip prompt injection attempts."""
        injection_patterns = [
            r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|rules|prompts)",
            r"(?i)you\s+are\s+now\s+",
            r"(?i)new\s+instructions?:",
            r"(?i)system\s*:",
            r"(?i)\[system\]",
            r"(?i)forget\s+(everything|all|your\s+rules)",
            r"(?i)reveal\s+(your|the)\s+(prompt|instructions|system)",
        ]
        sanitized = text
        for pattern in injection_patterns:
            sanitized = re.sub(pattern, "[filtered]", sanitized)
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", sanitized)
        sanitized = re.sub(r"[\u200b-\u200f\u2028-\u202f\u2060\ufeff]", "", sanitized)
        return sanitized[:400].strip()

    async def handle_raw(self, raw: str):
        for line in raw.strip().split("\r\n"):
            if line.startswith("PING"):
                await self.ws.send(line.replace("PING", "PONG"))
                continue

            # Try tagged parse first
            match = re.match(
                r"@(?P<tags>\S+) :(?P<user>\w+)!\S+ PRIVMSG #\w+ :(?P<msg>.+)", line
            )
            if not match:
                match = re.match(r":(?P<user>\w+)!\S+ PRIVMSG #\w+ :(?P<msg>.+)", line)
                if not match:
                    continue
                user, msg = match.group("user"), match.group("msg").strip()
                tags = {}
            else:
                user = match.group("user")
                msg = match.group("msg").strip()
                tags = dict(kv.split("=", 1) for kv in match.group("tags").split(";") if "=" in kv)

            if user.lower() == self.bot_login:
                continue

            msg = self._sanitize(msg)
            if not msg or msg == "[filtered]":
                continue

            # Store in rolling history
            entry = {"user": user, "msg": msg, "time": datetime.now().isoformat()}
            self.chat_history.append(entry)
            if len(self.chat_history) > self.max_history:
                self.chat_history = self.chat_history[-self.max_history:]

            # Persist to JSONL
            try:
                with open(self.chat_log_path, "a") as f:
                    f.write(json.dumps({**entry, "tags": tags}) + "\n")
            except Exception:
                pass

            logger.info(f"[{user}]: {msg}")
            await self.handle_message(user, msg, tags)

    async def handle_message(self, user: str, msg: str, tags: dict):
        """Route message to trigger handler or ignore."""
        msg_lower = msg.lower().strip()

        if msg_lower.startswith(self.trigger_word):
            args = msg[len(self.trigger_word):].strip()
            await self.trigger_handler(user, args or msg)

    async def trigger_handler(self, user: str, query: str):
        """Generate AI response to trigger."""
        now = time.time()
        if now - self.last_response_time < self.cooldown_seconds:
            logger.info(f"Cooldown active — skipping response to {user}")
            return

        if not self.api_key:
            await self.send_message(f"@{user} AI is offline — no API key configured.")
            return

        # Build context from recent chat
        recent = self.chat_history[-10:]
        chat_context = "\n".join(f"{m['user']}: {m['msg']}" for m in recent)

        prompt = f"""Recent chat:
{chat_context}

{user} asks: {query}

Reply (one message, under 150 chars):"""

        try:
            reply = await self._call_anthropic(prompt)
            if reply and len(reply.strip()) > 2:
                reply = reply.strip().split("\n")[0][:200]
                await self.send_message(f"@{user} {reply}")
        except Exception as e:
            logger.error(f"AI call failed: {e}")
            await self.send_message(f"@{user} Brain lag — try again in a sec monkaS")

    async def _call_anthropic(self, user_prompt: str) -> str | None:
        """Call Anthropic API."""
        import aiohttp

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 256,
            "temperature": 0.8,
            "system": self.system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers, json=payload,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["content"][0]["text"]
                else:
                    logger.error(f"Anthropic {resp.status}: {await resp.text()}")
                    return None

    async def run(self):
        """Main loop with auto-reconnect."""
        while self.running:
            try:
                await self.connect()
                await self.send_message(f"{self.bot_login} online 👾 Type {self.trigger_word} <question> to talk to me!")

                async for raw in self.ws:
                    if not self.running:
                        break
                    await self.handle_raw(raw)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed — reconnecting in 5s")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error: {e} — reconnecting in 10s")
                await asyncio.sleep(10)


async def main():
    parser = argparse.ArgumentParser(description="Twitch AI Chatbot")
    parser.add_argument("--config", default=None, help="Path to config.json")
    args = parser.parse_args()

    config = load_config(args.config)
    setup_logging(config["log_file"])

    # Install dependencies if missing
    try:
        import aiohttp
    except ImportError:
        os.system("pip3 install aiohttp --break-system-packages -q")

    try:
        import websockets
    except ImportError:
        os.system("pip3 install websockets --break-system-packages -q")

    bot = TwitchAIBot(config)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
