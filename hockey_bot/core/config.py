from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    bot_token: str
    allowed_telegram_user_id: int
    database_url: str = "sqlite:///hockey_bot.db"
    default_timezone: str = "Europe/Moscow"

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        user_id = os.getenv("ALLOWED_TELEGRAM_USER_ID", "0")
        return cls(
            bot_token=token,
            allowed_telegram_user_id=int(user_id),
            database_url=os.getenv("DATABASE_URL", "sqlite:///hockey_bot.db"),
            default_timezone=os.getenv("DEFAULT_TIMEZONE", "Europe/Moscow"),
        )

    @property
    def sqlite_path(self) -> Path | None:
        if not self.database_url.startswith("sqlite:///"):
            return None
        return Path(self.database_url.removeprefix("sqlite:///"))
