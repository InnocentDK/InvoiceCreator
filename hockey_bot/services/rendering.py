from __future__ import annotations

from calendar import monthcalendar
from datetime import date
from hockey_bot.bot.types import InlineKeyboardButton, InlineKeyboardMarkup

from hockey_bot.models.enums import EventType, RU_LABELS
from hockey_bot.models.tables import Event
from hockey_bot.services.events import total_expenses

MONTHS = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]


def format_rub(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " ₽"


def event_title(event: Event) -> str:
    if event.event_type in {EventType.GAME, EventType.AWAY_GAME}:
        return f"{RU_LABELS[event.event_type]} {event.own_team_name_snapshot or 'Моя команда'} — {event.opponent_name_snapshot or 'Соперник'}"
    return str(RU_LABELS[event.event_type])


def event_card(event: Event, expenses: int = 0) -> str:
    lines = [f"<b>{RU_LABELS[event.event_type]}</b>"]
    if event.league_name_snapshot:
        lines.append(f"🏆 {event.league_name_snapshot}")
    if event.event_type in {EventType.GAME, EventType.AWAY_GAME}:
        lines.append(f"🏒 {event.own_team_name_snapshot or 'Моя команда'} — {event.opponent_name_snapshot or 'Соперник'}")
    lines += [f"📅 {event.event_date:%d.%m.%Y}", f"⏰ {event.event_time:%H:%M}"]
    if event.arena_name_snapshot:
        lines.append(f"🏟 {event.arena_name_snapshot}")
    if event.arena_address_snapshot:
        lines.append(f"📍 {event.arena_address_snapshot}")
    if event.home_away:
        lines.append(f"🏠 {RU_LABELS[event.home_away]}")
    if event.score:
        lines.append(f"🟢 {RU_LABELS[event.result]} {event.score}")
    elif event.event_type in {EventType.GAME, EventType.AWAY_GAME}:
        lines.append(f"⚪ {RU_LABELS[event.result]}")
    lines.append(f"💰 Расходы: {format_rub(expenses)}")
    if event.comment:
        lines.append(event.comment)
    return "\n".join(lines)


def calendar_keyboard(year: int, month: int, event_days: set[int]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"📅 {MONTHS[month]} {year}", callback_data="noop")]]
    rows.append([InlineKeyboardButton(text=d, callback_data="noop") for d in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]])
    for week in monthcalendar(year, month):
        row = []
        for day in week:
            text = " " if day == 0 else (f"•{day}" if day in event_days else str(day))
            row.append(InlineKeyboardButton(text=text, callback_data="noop" if day == 0 else f"cal:day:{year}:{month}:{day}"))
        rows.append(row)
    prev_m, prev_y = (12, year - 1) if month == 1 else (month - 1, year)
    next_m, next_y = (1, year + 1) if month == 12 else (month + 1, year)
    today = date.today()
    rows.append([
        InlineKeyboardButton(text="◀️", callback_data=f"cal:month:{prev_y}:{prev_m}"),
        InlineKeyboardButton(text="Сегодня", callback_data=f"cal:month:{today.year}:{today.month}"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal:month:{next_y}:{next_m}"),
    ])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
