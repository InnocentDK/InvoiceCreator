from hockey_bot.bot.keyboards import add_keyboard, directory_keyboard, event_card_keyboard, expenses_keyboard, finance_keyboard, settings_keyboard, stats_keyboard, trash_keyboard
from hockey_bot.services.rendering import calendar_keyboard


def texts(markup):
    return [button.text for row in markup.inline_keyboard for button in row]


def test_all_menus_have_back_button():
    keyboards = [
        add_keyboard(),
        settings_keyboard(),
        directory_keyboard("leagues"),
        finance_keyboard(2026, 8),
        stats_keyboard(),
        event_card_keyboard(1),
        expenses_keyboard(1),
        trash_keyboard([1]),
        calendar_keyboard(2026, 8, {25}),
    ]
    for keyboard in keyboards:
        assert "⬅️ Назад" in texts(keyboard)
