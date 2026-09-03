"""Environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    jwt_secret: str
    access_token_minutes: int
    log_level: str
    agent_mode: str


@lru_cache
def get_settings() -> Settings:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET must be set and contain at least 32 characters")

    minutes = int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))
    if minutes < 1 or minutes > 1440:
        raise RuntimeError("ACCESS_TOKEN_MINUTES must be between 1 and 1440")

    mode = os.getenv("AGENT_MODE", "offline").lower()
    if mode not in {"offline", "online"}:
        raise RuntimeError("AGENT_MODE must be 'offline' or 'online'")

    return Settings(
        jwt_secret=secret,
        access_token_minutes=minutes,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        agent_mode=mode,
    )

