"""Runtime configuration for the booth app.

Everything has a safe default so the app runs offline at the booth with zero
setup. Set ANTHROPIC_API_KEY only if you want the live Claude-powered bot.
"""

import os


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


# Live bot is enabled only when a key is present. Otherwise the deterministic
# offline bot is used — the booth never depends on venue Wi-Fi.
ANTHROPIC_API_KEY: str = _get("ANTHROPIC_API_KEY")

# Default to the latest, most capable Claude model. A high-volume booth may
# switch to claude-haiku-4-5 for speed/cost via ANTHROPIC_MODEL.
ANTHROPIC_MODEL: str = _get("ANTHROPIC_MODEL", "claude-opus-4-8")

LIVE_BOT_ENABLED: bool = bool(ANTHROPIC_API_KEY)

HOST: str = _get("HOST", "0.0.0.0")
PORT: int = int(_get("PORT", "8000") or "8000")

# Branding (from the booth runbook).
EVENT_NAME = "Ai4 2026 · The Venetian, Las Vegas"
PRODUCT_NAME = "TrendAI Vision One"
APP_TITLE = "Vision One AI Security Challenge"
