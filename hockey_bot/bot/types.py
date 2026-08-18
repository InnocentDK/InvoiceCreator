from __future__ import annotations

try:
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
except ModuleNotFoundError:  # pragma: no cover - lightweight test fallback when Telegram deps are absent
    class InlineKeyboardButton:
        def __init__(self, text: str, callback_data: str):
            self.text = text
            self.callback_data = callback_data

    class InlineKeyboardMarkup:
        def __init__(self, inline_keyboard):
            self.inline_keyboard = inline_keyboard
