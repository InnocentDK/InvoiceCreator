from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

MAIN = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📅 Календарь", callback_data="calendar"), InlineKeyboardButton(text="➕ Добавить", callback_data="add")],
    [InlineKeyboardButton(text="💰 Финансы", callback_data="finance"), InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
    [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
])

ADD = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🏒 Тренировка", callback_data="add:training"), InlineKeyboardButton(text="🏒 Двухсторонка", callback_data="add:scrimmage")],
    [InlineKeyboardButton(text="🏆 Игра", callback_data="add:game"), InlineKeyboardButton(text="🚌 Выездная игра", callback_data="add:away_game")],
])

SETTINGS = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👤 Моя команда", callback_data="settings:own_team"), InlineKeyboardButton(text="🏆 Лиги", callback_data="settings:leagues")],
    [InlineKeyboardButton(text="🏒 Команды", callback_data="settings:teams"), InlineKeyboardButton(text="🏟 Арены", callback_data="settings:arenas")],
    [InlineKeyboardButton(text="📅 Сезоны", callback_data="settings:seasons"), InlineKeyboardButton(text="🌍 Часовой пояс", callback_data="settings:timezone")],
    [InlineKeyboardButton(text="🗑 Корзина", callback_data="settings:trash"), InlineKeyboardButton(text="📊 Экспорт в Excel", callback_data="settings:export")],
])
