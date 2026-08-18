from __future__ import annotations

from datetime import datetime
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from hockey_bot.bot.keyboards import ADD, MAIN, SETTINGS
from hockey_bot.core.config import Settings
from hockey_bot.models.tables import User
from hockey_bot.services.events import upcoming_events
from hockey_bot.services.rendering import event_title


def build_router(settings: Settings, sessions: sessionmaker) -> Router:
    router = Router()

    async def authorized(tg_id: int) -> bool:
        return settings.allowed_telegram_user_id == tg_id

    @router.message(CommandStart())
    async def start(message: Message):
        if not await authorized(message.from_user.id):
            await message.answer("⛔ Доступ запрещён")
            return
        with sessions() as session:
            user = session.scalar(select(User).where(User.telegram_user_id == message.from_user.id))
            if not user:
                user = User(telegram_user_id=message.from_user.id, timezone=settings.default_timezone)
                session.add(user); session.commit()
            events = upcoming_events(session, user.id, datetime.now(), 3)
        lines = ["<b>🏒 Мой хоккей</b>", ""] + ([event_title(e) for e in events] or ["Ближайших событий пока нет"])
        await message.answer("\n".join(lines), reply_markup=MAIN)

    @router.callback_query(lambda c: c.data == "add")
    async def add(callback: CallbackQuery):
        await callback.message.edit_text("Что добавить?", reply_markup=ADD)
        await callback.answer()

    @router.callback_query(lambda c: c.data == "settings")
    async def settings_menu(callback: CallbackQuery):
        await callback.message.edit_text("⚙️ Настройки", reply_markup=SETTINGS)
        await callback.answer()

    @router.callback_query()
    async def placeholder(callback: CallbackQuery):
        await callback.answer("Раздел подготовлен. Используйте сервисный слой для сценариев создания и редактирования.", show_alert=True)

    return router
