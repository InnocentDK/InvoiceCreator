from __future__ import annotations

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from hockey_bot.bot.handlers import build_router
from hockey_bot.core.config import Settings
from hockey_bot.db.init_db import init_db
from hockey_bot.db.session import make_session_factory


async def main() -> None:
    settings = Settings.from_env()
    if not settings.bot_token or not settings.allowed_telegram_user_id:
        raise RuntimeError("Заполните TELEGRAM_BOT_TOKEN и ALLOWED_TELEGRAM_USER_ID")
    init_db(settings.database_url)
    sessions = make_session_factory(settings.database_url)
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(build_router(settings, sessions))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
