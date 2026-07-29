from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT_KEYWORDS = (
    "developer,software engineer,backend,frontend,full stack,fullstack,devops,"
    "site reliability,sre,qa engineer,mobile developer,ios developer,android developer,"
    "cloud engineer,platform engineer,machine learning engineer,data engineer"
)


def _split_env(name: str, default: str = "") -> tuple[str, ...]:
    raw = os.environ.get(name, default)
    parts = [p.strip() for p in raw.split(",")]
    return tuple(p for p in parts if p)


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    keywords: tuple[str, ...] = field(default_factory=tuple)
    require_remote: bool = True
    request_timeout: int = 20
    request_retries: int = 3
    state_path: Path = field(default_factory=lambda: Path("state.json"))
    dry_run: bool = False
    user_agent: str = "remote-jobs-bot/1.0 (+https://github.com/)"
    max_offers_per_run: int = 30
    telegram_message_limit: int = 4000
    log_level: str = "INFO"
    only_junior: bool = True

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN") or None,
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID") or None,
            keywords=tuple(k.lower() for k in _split_env("BOT_KEYWORDS", _DEFAULT_KEYWORDS)),
            require_remote=_bool_env("BOT_REQUIRE_REMOTE", True),
            request_timeout=_int_env("BOT_REQUEST_TIMEOUT", 20),
            request_retries=_int_env("BOT_REQUEST_RETRIES", 3),
            state_path=Path(os.environ.get("BOT_STATE_PATH", "state.json")),
            dry_run=_bool_env("BOT_DRY_RUN", False),
            max_offers_per_run=_int_env("BOT_MAX_OFFERS", 30),
            telegram_message_limit=_int_env("BOT_TG_LIMIT", 4000),
            log_level=os.environ.get("BOT_LOG_LEVEL", "INFO"),
            only_junior=_bool_env("BOT_ONLY_JUNIOR", True),
        )

    def can_send_telegram(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)
