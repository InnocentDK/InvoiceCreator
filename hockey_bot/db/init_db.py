from __future__ import annotations

from hockey_bot.core.config import Settings
from hockey_bot.db.session import Base, make_engine
import hockey_bot.models.tables  # noqa: F401


def init_db(database_url: str | None = None) -> None:
    Base.metadata.create_all(make_engine(database_url or Settings.from_env().database_url))


if __name__ == "__main__":
    init_db()
