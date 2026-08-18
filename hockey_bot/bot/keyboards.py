from __future__ import annotations

from hockey_bot.bot.types import InlineKeyboardButton, InlineKeyboardMarkup

BACK_TO_MAIN = InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:main")
BACK_TO_SETTINGS = InlineKeyboardButton(text="⬅️ Назад", callback_data="settings")


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Календарь", callback_data="calendar"), InlineKeyboardButton(text="➕ Добавить", callback_data="add")],
        [InlineKeyboardButton(text="💰 Финансы", callback_data="finance"), InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
    ])


def add_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏒 Тренировка", callback_data="add:training"), InlineKeyboardButton(text="🏒 Двухсторонка", callback_data="add:scrimmage")],
        [InlineKeyboardButton(text="🏆 Игра", callback_data="add:game"), InlineKeyboardButton(text="🚌 Выездная игра", callback_data="add:away_game")],
        [BACK_TO_MAIN],
    ])


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Моя команда", callback_data="settings:own_team"), InlineKeyboardButton(text="🏆 Лиги", callback_data="settings:leagues")],
        [InlineKeyboardButton(text="🏒 Команды", callback_data="settings:teams"), InlineKeyboardButton(text="🏟 Арены", callback_data="settings:arenas")],
        [InlineKeyboardButton(text="📅 Сезоны", callback_data="settings:seasons"), InlineKeyboardButton(text="🌍 Часовой пояс", callback_data="settings:timezone")],
        [InlineKeyboardButton(text="🗑 Корзина", callback_data="settings:trash"), InlineKeyboardButton(text="📊 Экспорт в Excel", callback_data="settings:export")],
        [BACK_TO_MAIN],
    ])


def directory_keyboard(kind: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить новую", callback_data=f"dir:{kind}:new")],
        [InlineKeyboardButton(text="♻️ Показать архив", callback_data=f"dir:{kind}:archived")],
        [BACK_TO_SETTINGS],
    ])


def finance_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    prev_month = 12 if month == 1 else month - 1
    prev_year = year - 1 if month == 1 else year
    next_month = 1 if month == 12 else month + 1
    next_year = year + 1 if month == 12 else year
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Все", callback_data=f"finance:{year}:{month}:all"), InlineKeyboardButton(text="Игры", callback_data=f"finance:{year}:{month}:games"), InlineKeyboardButton(text="Тренировки", callback_data=f"finance:{year}:{month}:trainings")],
        [InlineKeyboardButton(text="◀️", callback_data=f"finance:{prev_year}:{prev_month}:all"), InlineKeyboardButton(text="▶️", callback_data=f"finance:{next_year}:{next_month}:all")],
        [BACK_TO_MAIN],
    ])


def stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Всё время", callback_data="stats:all"), InlineKeyboardButton(text="По лигам", callback_data="stats:leagues")],
        [InlineKeyboardButton(text="По сезонам", callback_data="stats:seasons"), InlineKeyboardButton(text="По типам", callback_data="stats:types")],
        [BACK_TO_MAIN],
    ])


def event_card_keyboard(event_id: int, back_callback: str = "calendar") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить", callback_data=f"event:{event_id}:edit"), InlineKeyboardButton(text="💰 Расходы", callback_data=f"event:{event_id}:expenses")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"event:{event_id}:delete")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback)],
    ])


def expenses_keyboard(event_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить расход", callback_data=f"event:{event_id}:expense:new")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"event:{event_id}")],
    ])


def delete_confirm_keyboard(event_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"event:{event_id}"), InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"event:{event_id}:delete:confirm")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"event:{event_id}")],
    ])


def trash_keyboard(event_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"♻️ Восстановить #{event_id}", callback_data=f"trash:restore:{event_id}")] for event_id in event_ids]
    rows.append([BACK_TO_SETTINGS])
    return InlineKeyboardMarkup(inline_keyboard=rows)
