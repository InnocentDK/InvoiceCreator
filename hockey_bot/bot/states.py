from __future__ import annotations

try:
    from aiogram.fsm.state import State, StatesGroup
except ModuleNotFoundError:  # pragma: no cover
    class State:
        pass

    class StatesGroup:
        pass


class DirectoryForm(StatesGroup):
    kind = State()
    name = State()
    arena_address = State()


class EventForm(StatesGroup):
    event_type = State()
    date = State()
    time = State()
    team = State()
    league = State()
    opponent = State()
    home_away = State()
    arena = State()
    season = State()
    cost = State()
    recurrence = State()
    recurrence_end = State()
    comment = State()
    confirm = State()


class ExpenseForm(StatesGroup):
    event_id = State()
    amount = State()


class ScoreForm(StatesGroup):
    event_id = State()
    score = State()
