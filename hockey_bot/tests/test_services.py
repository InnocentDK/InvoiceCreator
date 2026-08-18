from datetime import date, time, datetime

import pytest

from hockey_bot.db.init_db import init_db
from hockey_bot.db.session import make_session_factory
from hockey_bot.models.enums import EventType, GameResult, HomeAway, RecurrenceRule
from hockey_bot.models.tables import Arena, League, Team, User
from hockey_bot.services.directories import create_named, set_own_team
from hockey_bot.services.events import EventDraft, add_expense, create_event, create_recurring_events, restore_event, set_game_score, soft_delete_event, upcoming_events
from hockey_bot.services.statistics import finance_month, sports_stats
from hockey_bot.services.validation import parse_score


@pytest.fixture()
def session(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    init_db(url)
    Session = make_session_factory(url)
    with Session() as s:
        yield s


def seed(session):
    user = User(telegram_user_id=1, timezone="Europe/Moscow")
    session.add(user); session.commit()
    own = create_named(session, Team, "ХК Север")
    opp = create_named(session, Team, "Динамо")
    league = create_named(session, League, "Ночная лига")
    arena = create_named(session, Arena, "Арена Север", address="ул. Ледовая, 1")
    set_own_team(session, user, own.id)
    return user, own, opp, league, arena


def test_score_result_home_and_away(session):
    user, own, opp, league, arena = seed(session)
    home = create_event(session, EventDraft(user.id, EventType.GAME, date(2026, 8, 25), time(20), league_id=league.id, own_team_id=own.id, opponent_team_id=opp.id, arena_id=arena.id, home_away=HomeAway.HOME))
    away = create_event(session, EventDraft(user.id, EventType.AWAY_GAME, date(2026, 8, 26), time(20), league_id=league.id, own_team_id=own.id, opponent_team_id=opp.id, arena_id=arena.id, home_away=HomeAway.AWAY))
    assert set_game_score(session, home.id, "5:3").result == GameResult.WIN
    assert set_game_score(session, away.id, "3:5").result == GameResult.WIN
    with pytest.raises(ValueError):
        parse_score("2:2")


def test_recurring_soft_delete_restore_and_stats(session):
    user, own, _opp, _league, arena = seed(session)
    draft = EventDraft(user.id, EventType.TRAINING, date(2026, 9, 1), time(20), team_id=own.id, arena_id=arena.id, cost_rub=800)
    events = create_recurring_events(session, draft, RecurrenceRule.WEEKLY, date(2026, 9, 22))
    assert len(events) == 4
    assert soft_delete_event(session, events[1].id)
    assert len(upcoming_events(session, user.id, datetime(2026, 8, 1), 10)) == 3
    assert restore_event(session, events[1].id)
    add_expense(session, events[0].id, 800)
    assert finance_month(session, user.id, date(2026, 9, 1), date(2026, 9, 30))["trainings"] == 800
    assert sports_stats(session, user.id)["training_count"] == 4


def test_create_named_is_idempotent(session):
    first = create_named(session, Team, "ХК Север")
    second = create_named(session, Team, "ХК Север")
    assert first.id == second.id
