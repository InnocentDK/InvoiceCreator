from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from pathlib import Path

from aiogram import Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from hockey_bot.bot.states import DirectoryForm, EventForm, ExpenseForm, ScoreForm
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
from hockey_bot.services.events import EventDraft, add_expense, create_event, create_recurring_events, month_events, restore_event, set_game_score, soft_delete_event, total_expenses, upcoming_events
from hockey_bot.services.rendering import MONTHS, calendar_keyboard, event_card, event_title, format_rub
from hockey_bot.services.statistics import finance_month, sports_stats
from hockey_bot.services.directories import create_named
from hockey_bot.models.enums import EventType, HomeAway, RecurrenceRule
from hockey_bot.services.validation import parse_non_negative_amount, parse_ru_date, parse_time

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
    async def nav_main(callback: CallbackQuery, state: FSMContext):
        await state.clear()
        await show_main(callback)

    @router.callback_query(lambda c: c.data == "add")
    async def add(callback: CallbackQuery):
        await callback.message.edit_text("➕ Что добавить?", reply_markup=add_keyboard())
        await callback.answer()

    @router.callback_query(lambda c: c.data and c.data.startswith("add:"))
    async def add_placeholder(callback: CallbackQuery, state: FSMContext):
        event_type = callback.data.split(":", 1)[1]
        await state.set_state(EventForm.date)
        await state.update_data(event_type=event_type)
        await callback.message.edit_text("Введите дату события в формате ДД.ММ.ГГГГ", reply_markup=add_keyboard())
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
        if action == "expense" and len(parts) > 3 and parts[3] == "new":
            await callback.answer()
            return
        if action == "edit":
            await callback.answer("Редактирование будет выполнено через сервис update_event_fields; используйте создание заново для MVP.", show_alert=True)
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

    @router.callback_query(lambda c: c.data and c.data.startswith("dir:") and c.data.endswith(":new"))
    async def directory_new(callback: CallbackQuery, state: FSMContext):
        kind = callback.data.split(":")[1]
        await state.set_state(DirectoryForm.name)
        await state.update_data(kind=kind)
        await callback.message.edit_text("Введите название", reply_markup=directory_keyboard(kind))
        await callback.answer()

    @router.message(DirectoryForm.name)
    async def directory_name(message: Message, state: FSMContext):
        data = await state.get_data()
        kind = data["kind"]
        if kind == "arenas":
            await state.update_data(name=message.text.strip())
            await state.set_state(DirectoryForm.arena_address)
            await message.answer("Введите адрес арены")
            return
        model, title = DIRECTORY_MODELS[kind]
        with sessions() as session:
            create_named(session, model, message.text)
        await state.clear()
        await message.answer(f"✅ {title}: сохранено", reply_markup=settings_keyboard())

    @router.message(DirectoryForm.arena_address)
    async def arena_address(message: Message, state: FSMContext):
        data = await state.get_data()
        with sessions() as session:
            create_named(session, Arena, data["name"], address=message.text.strip())
        await state.clear()
        await message.answer("✅ Арена сохранена", reply_markup=settings_keyboard())

    @router.message(EventForm.date)
    async def event_date(message: Message, state: FSMContext):
        try:
            value = parse_ru_date(message.text)
        except ValueError as exc:
            await message.answer(str(exc))
            return
        await state.update_data(date=value)
        await state.set_state(EventForm.time)
        await message.answer("Введите время в формате ЧЧ:ММ")

    @router.message(EventForm.time)
    async def event_time(message: Message, state: FSMContext):
        try:
            value = parse_time(message.text)
        except ValueError as exc:
            await message.answer(str(exc))
            return
        await state.update_data(time=value)
        data = await state.get_data()
        if data["event_type"] in {"game", "away_game"}:
            await state.set_state(EventForm.opponent)
            await message.answer("Введите название соперника")
        elif data["event_type"] == "training":
            await state.set_state(EventForm.team)
            await message.answer("Введите название команды для тренировки")
        else:
            await state.set_state(EventForm.arena)
            await message.answer("Введите название арены")

    @router.message(EventForm.team)
    async def event_team(message: Message, state: FSMContext):
        await state.update_data(team_name=message.text.strip())
        await state.set_state(EventForm.arena)
        await message.answer("Введите название арены")

    @router.message(EventForm.opponent)
    async def event_opponent(message: Message, state: FSMContext):
        await state.update_data(opponent_name=message.text.strip())
        await state.set_state(EventForm.home_away)
        await message.answer("Где игра? Напишите: дома или выезд")

    @router.message(EventForm.home_away)
    async def event_home_away(message: Message, state: FSMContext):
        text = message.text.lower().strip()
        if text not in {"дома", "выезд", "на выезде"}:
            await message.answer("Введите `дома` или `выезд`")
            return
        await state.update_data(home_away=HomeAway.HOME if text == "дома" else HomeAway.AWAY)
        await state.set_state(EventForm.arena)
        await message.answer("Введите название арены")

    @router.message(EventForm.arena)
    async def event_arena(message: Message, state: FSMContext):
        await state.update_data(arena_name=message.text.strip())
        await state.set_state(EventForm.cost)
        await message.answer("Введите стоимость/плановый расход числом, можно 0")

    @router.message(EventForm.cost)
    async def event_cost(message: Message, state: FSMContext):
        try:
            cost = parse_non_negative_amount(message.text)
        except ValueError as exc:
            await message.answer(str(exc))
            return
        data = await state.get_data()
        event_type = data["event_type"]
        with sessions() as session:
            user = get_or_create_user(session, message.from_user.id)
            arena = create_named(session, Arena, data.get("arena_name") or "Без арены")
            team = None
            opponent = None
            own_team_id = user.current_own_team_id
            if data.get("team_name"):
                team = create_named(session, Team, data["team_name"])
            if data.get("opponent_name"):
                opponent = create_named(session, Team, data["opponent_name"])
            draft = EventDraft(
                user_id=user.id,
                event_type=EventType(event_type),
                event_date=data["date"],
                event_time=data["time"],
                team_id=team.id if team else None,
                opponent_team_id=opponent.id if opponent else None,
                own_team_id=own_team_id,
                arena_id=arena.id,
                home_away=data.get("home_away"),
                cost_rub=cost,
            )
            event = create_event(session, draft)
            if cost:
                add_expense(session, event.id, cost)
        await state.clear()
        await message.answer(f"✅ Событие создано: #{event.id}", reply_markup=main_keyboard())

    @router.callback_query(lambda c: c.data and c.data.startswith("event:") and c.data.endswith(":expense:new"))
    async def expense_new(callback: CallbackQuery, state: FSMContext):
        event_id = int(callback.data.split(":")[1])
        await state.set_state(ExpenseForm.amount)
        await state.update_data(event_id=event_id)
        await callback.message.edit_text("Введите сумму расхода числом")
        await callback.answer()

    @router.message(ExpenseForm.amount)
    async def expense_amount(message: Message, state: FSMContext):
        try:
            amount = parse_non_negative_amount(message.text)
        except ValueError as exc:
            await message.answer(str(exc))
            return
        data = await state.get_data()
        with sessions() as session:
            add_expense(session, data["event_id"], amount)
        await state.clear()
        await message.answer("✅ Расход добавлен", reply_markup=main_keyboard())

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
