from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from pathlib import Path

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, FSInputFile, Message
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from hockey_bot.bot.keyboards import (
    add_keyboard,
    delete_confirm_keyboard,
    directory_keyboard,
    event_card_keyboard,
    expenses_keyboard,
    finance_keyboard,
    main_keyboard,
    settings_keyboard,
    stats_keyboard,
    trash_keyboard,
)
from hockey_bot.core.config import Settings
from hockey_bot.excel.exporter import export_excel
from hockey_bot.models.tables import Arena, Event, Expense, League, Season, Team, User
from hockey_bot.services.events import month_events, restore_event, soft_delete_event, total_expenses, upcoming_events
from hockey_bot.services.rendering import MONTHS, calendar_keyboard, event_card, event_title, format_rub
from hockey_bot.services.statistics import finance_month, sports_stats

DIRECTORY_MODELS = {
    "leagues": (League, "🏆 Лиги"),
    "teams": (Team, "🏒 Команды"),
    "arenas": (Arena, "🏟 Арены"),
    "seasons": (Season, "📅 Сезоны"),
}


def build_router(settings: Settings, sessions: sessionmaker) -> Router:
    router = Router()

    async def authorized(tg_id: int) -> bool:
        return settings.allowed_telegram_user_id == tg_id

    def get_or_create_user(session, telegram_user_id: int) -> User:
        user = session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))
        if not user:
            user = User(telegram_user_id=telegram_user_id, timezone=settings.default_timezone)
            session.add(user)
            session.commit()
        return user

    def main_text(session, user: User) -> str:
        events = upcoming_events(session, user.id, datetime.now(), 3)
        lines = ["<b>🏒 Мой хоккей</b>", ""]
        if events:
            lines.extend(event_title(e) for e in events)
        else:
            lines.append("Ближайших событий пока нет")
        return "\n".join(lines)

    async def show_main(target: Message | CallbackQuery) -> None:
        telegram_user_id = target.from_user.id
        if not await authorized(telegram_user_id):
            if isinstance(target, CallbackQuery):
                await target.answer("⛔ Доступ запрещён", show_alert=True)
            else:
                await target.answer("⛔ Доступ запрещён")
            return
        with sessions() as session:
            user = get_or_create_user(session, telegram_user_id)
            text = main_text(session, user)
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(text, reply_markup=main_keyboard())
            await target.answer()
        else:
            await target.answer(text, reply_markup=main_keyboard())

    @router.message(CommandStart())
    async def start(message: Message):
        await show_main(message)

    @router.callback_query(lambda c: c.data == "nav:main")
    async def nav_main(callback: CallbackQuery):
        await show_main(callback)

    @router.callback_query(lambda c: c.data == "add")
    async def add(callback: CallbackQuery):
        await callback.message.edit_text("➕ Что добавить?", reply_markup=add_keyboard())
        await callback.answer()

    @router.callback_query(lambda c: c.data and c.data.startswith("add:"))
    async def add_placeholder(callback: CallbackQuery):
        await callback.message.edit_text(
            "Пошаговый сценарий добавления будет открыт здесь.\n"
            "Все экраны добавления теперь содержат кнопку возврата назад.",
            reply_markup=add_keyboard(),
        )
        await callback.answer()

    @router.callback_query(lambda c: c.data == "calendar")
    async def calendar(callback: CallbackQuery):
        today = date.today()
        await show_calendar(callback, today.year, today.month)

    @router.callback_query(lambda c: c.data and c.data.startswith("cal:month:"))
    async def calendar_month(callback: CallbackQuery):
        _, _, year, month = callback.data.split(":")
        await show_calendar(callback, int(year), int(month))

    async def show_calendar(callback: CallbackQuery, year: int, month: int) -> None:
        with sessions() as session:
            user = get_or_create_user(session, callback.from_user.id)
            events = month_events(session, user.id, year, month)
            event_days = {event.event_date.day for event in events}
        await callback.message.edit_text(f"📅 {MONTHS[month]} {year}", reply_markup=calendar_keyboard(year, month, event_days))
        await callback.answer()

    @router.callback_query(lambda c: c.data and c.data.startswith("cal:day:"))
    async def calendar_day(callback: CallbackQuery):
        _, _, year, month, day = callback.data.split(":")
        selected = date(int(year), int(month), int(day))
        with sessions() as session:
            user = get_or_create_user(session, callback.from_user.id)
            events = [e for e in month_events(session, user.id, selected.year, selected.month) if e.event_date == selected]
        if not events:
            await callback.answer("На эту дату событий нет", show_alert=True)
            return
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        rows = [[InlineKeyboardButton(text=event_title(e), callback_data=f"event:{e.id}:from:cal:day:{selected.year}:{selected.month}:{selected.day}")] for e in events]
        rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cal:month:{selected.year}:{selected.month}")])
        await callback.message.edit_text(f"📅 {selected:%d.%m.%Y}", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
        await callback.answer()

    @router.callback_query(lambda c: c.data and c.data.startswith("event:"))
    async def event_actions(callback: CallbackQuery):
        parts = callback.data.split(":")
        event_id = int(parts[1])
        action = parts[2] if len(parts) > 2 else "view"
        if action == "delete":
            if len(parts) > 3 and parts[3] == "confirm":
                with sessions() as session:
                    ok = soft_delete_event(session, event_id)
                await callback.message.edit_text("🗑 Событие перемещено в корзину" if ok else "Событие не найдено", reply_markup=main_keyboard())
            else:
                await callback.message.edit_text("⚠️ Удалить событие?", reply_markup=delete_confirm_keyboard(event_id))
            await callback.answer()
            return
        if action == "expenses":
            with sessions() as session:
                expenses = list(session.scalars(select(Expense).where(Expense.event_id == event_id).order_by(Expense.created_at)))
                total = sum(e.amount_rub for e in expenses)
            lines = ["💰 Расходы", f"Всего: {format_rub(total)}"] + [f"• {format_rub(e.amount_rub)}" for e in expenses]
            await callback.message.edit_text("\n".join(lines), reply_markup=expenses_keyboard(event_id))
            await callback.answer()
            return
        if action in {"edit", "expense"}:
            await callback.answer("Пошаговый ввод будет добавлен следующим этапом; кнопка Назад уже доступна.", show_alert=True)
            return
        with sessions() as session:
            event = session.get(Event, event_id)
            if not event:
                await callback.answer("Событие не найдено", show_alert=True)
                return
            text = event_card(event, total_expenses(session, event.id))
        await callback.message.edit_text(text, reply_markup=event_card_keyboard(event_id))
        await callback.answer()

    @router.callback_query(lambda c: c.data == "finance" or (c.data and c.data.startswith("finance:")))
    async def finance(callback: CallbackQuery):
        if callback.data == "finance":
            today = date.today(); year, month, category = today.year, today.month, "all"
        else:
            _, year, month, category = callback.data.split(":")
            year, month = int(year), int(month)
        start = date(year, month, 1); end = date(year, month, monthrange(year, month)[1])
        with sessions() as session:
            user = get_or_create_user(session, callback.from_user.id)
            totals = finance_month(session, user.id, start, end)
        lines = [f"<b>💰 {MONTHS[month]} {year}</b>", f"Игры — {format_rub(totals['games'])}", f"Тренировки — {format_rub(totals['trainings'])}", f"<b>Всего — {format_rub(totals['total'])}</b>"]
        if category != "all":
            lines.append(f"\nФильтр: {'Игры' if category == 'games' else 'Тренировки'}")
        await callback.message.edit_text("\n".join(lines), reply_markup=finance_keyboard(year, month))
        await callback.answer()

    @router.callback_query(lambda c: c.data == "stats" or (c.data and c.data.startswith("stats:")))
    async def stats(callback: CallbackQuery):
        with sessions() as session:
            user = get_or_create_user(session, callback.from_user.id)
            data = sports_stats(session, user.id)
        text = "\n".join([
            "<b>📊 Статистика</b>",
            f"Тренировки: {data['training_count']}",
            f"Присутствовал: {data['present']}",
            f"Игры: {data['game_count']}",
            f"Победы: {data['wins']}",
            f"Поражения: {data['losses']}",
            f"Win rate: {data['win_rate']}%",
            f"Расходы: {format_rub(int(data['expenses']))}",
        ])
        await callback.message.edit_text(text, reply_markup=stats_keyboard())
        await callback.answer()

    @router.callback_query(lambda c: c.data == "settings")
    async def settings_menu(callback: CallbackQuery):
        await callback.message.edit_text("⚙️ Настройки", reply_markup=settings_keyboard())
        await callback.answer()

    @router.callback_query(lambda c: c.data and c.data.startswith("settings:"))
    async def settings_section(callback: CallbackQuery):
        kind = callback.data.split(":", 1)[1]
        if kind == "trash":
            with sessions() as session:
                user = get_or_create_user(session, callback.from_user.id)
                deleted = list(session.scalars(select(Event).where(Event.user_id == user.id, Event.deleted_at.is_not(None)).order_by(Event.deleted_at.desc()).limit(10)))
            text = "🗑 Корзина\n" + ("\n".join(f"#{e.id} — {event_title(e)}" for e in deleted) if deleted else "Корзина пуста")
            await callback.message.edit_text(text, reply_markup=trash_keyboard([e.id for e in deleted]))
        elif kind == "export":
            with sessions() as session:
                user = get_or_create_user(session, callback.from_user.id)
                out = Path(f"hockey_export_{user.id}.xlsx")
                export_excel(session, user.id, out)
            await callback.message.answer_document(FSInputFile(out), caption="📊 Экспорт в Excel готов")
            await callback.message.edit_text("⚙️ Настройки", reply_markup=settings_keyboard())
        elif kind in DIRECTORY_MODELS:
            model, title = DIRECTORY_MODELS[kind]
            with sessions() as session:
                objects = list(session.scalars(select(model).where(model.archived.is_(False)).order_by(model.name)))
            body = "\n".join(f"• {obj.name}" for obj in objects) if objects else "Пока нет данных"
            await callback.message.edit_text(f"{title}\n{body}", reply_markup=directory_keyboard(kind))
        else:
            await callback.message.edit_text("Раздел подготовлен для следующего шага настройки.", reply_markup=settings_keyboard())
        await callback.answer()

    @router.callback_query(lambda c: c.data and c.data.startswith("trash:restore:"))
    async def restore_from_trash(callback: CallbackQuery):
        event_id = int(callback.data.rsplit(":", 1)[1])
        with sessions() as session:
            ok = restore_event(session, event_id)
            user = get_or_create_user(session, callback.from_user.id)
            deleted = list(session.scalars(select(Event).where(Event.user_id == user.id, Event.deleted_at.is_not(None)).order_by(Event.deleted_at.desc()).limit(10)))
        text = "🗑 Корзина\n" + ("\n".join(f"#{e.id} — {event_title(e)}" for e in deleted) if deleted else "Корзина пуста")
        await callback.message.edit_text(text, reply_markup=trash_keyboard([e.id for e in deleted]))
        await callback.answer("Событие восстановлено" if ok else "Событие не найдено", show_alert=True)

    @router.callback_query(lambda c: c.data == "noop")
    async def noop(callback: CallbackQuery):
        await callback.answer()

    return router
