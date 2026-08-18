from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from calendar import monthrange

from hockey_bot.models.enums import AttendanceStatus, EventStatus, EventType, GameParticipation, GameResult, HomeAway, RecurrenceRule
from hockey_bot.models.tables import Arena, Event, EventRecurrence, Expense, League, Season, Team, User
from hockey_bot.services.validation import parse_score
from hockey_bot.services.times import utcnow_naive


@dataclass(frozen=True)
class EventDraft:
    user_id: int
    event_type: EventType
    event_date: date
    event_time: object
    team_id: int | None = None
    league_id: int | None = None
    season_id: int | None = None
    opponent_team_id: int | None = None
    own_team_id: int | None = None
    arena_id: int | None = None
    home_away: HomeAway | None = None
    cost_rub: int = 0
    comment: str | None = None


def _snapshot(session: Session, event: Event) -> None:
    if event.league_id:
        event.league_name_snapshot = session.get(League, event.league_id).name
    if event.own_team_id:
        event.own_team_name_snapshot = session.get(Team, event.own_team_id).name
    if event.opponent_team_id:
        event.opponent_name_snapshot = session.get(Team, event.opponent_team_id).name
    if event.team_id and not event.own_team_name_snapshot:
        event.own_team_name_snapshot = session.get(Team, event.team_id).name
    if event.arena_id:
        arena = session.get(Arena, event.arena_id)
        event.arena_name_snapshot = arena.name
        event.arena_address_snapshot = arena.address
    if event.season_id:
        event.season_name_snapshot = session.get(Season, event.season_id).name


def create_event(session: Session, draft: EventDraft) -> Event:
    event = Event(**draft.__dict__)
    if event.event_type == EventType.AWAY_GAME and event.home_away is None:
        event.home_away = HomeAway.AWAY
    _snapshot(session, event)
    session.add(event)
    session.commit()
    return event


def create_recurring_events(session: Session, draft: EventDraft, rule: RecurrenceRule, end_date: date) -> list[Event]:
    if rule == RecurrenceRule.NONE:
        return [create_event(session, draft)]
    recurrence = EventRecurrence(rule=rule, start_date=draft.event_date, end_date=end_date)
    session.add(recurrence)
    session.flush()
    step = {RecurrenceRule.WEEKLY: timedelta(days=7), RecurrenceRule.BIWEEKLY: timedelta(days=14)}.get(rule)
    current = draft.event_date
    events: list[Event] = []
    while current <= end_date:
        d = EventDraft(**{**draft.__dict__, "event_date": current})
        event = Event(**d.__dict__, recurrence_id=recurrence.id)
        _snapshot(session, event)
        session.add(event)
        events.append(event)
        if rule == RecurrenceRule.MONTHLY:
            month = current.month + 1
            year = current.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(current.day, monthrange(year, month)[1])
            current = date(year, month, day)
        else:
            current += step
    session.commit()
    return events


def soft_delete_event(session: Session, event_id: int) -> bool:
    event = session.get(Event, event_id)
    if not event or event.deleted_at:
        return False
    event.deleted_at = utcnow_naive()
    session.commit()
    return True


def restore_event(session: Session, event_id: int) -> bool:
    event = session.get(Event, event_id)
    if not event or not event.deleted_at:
        return False
    event.deleted_at = None
    session.commit()
    return True


def upcoming_events(session: Session, user_id: int, now: datetime, limit: int = 3) -> list[Event]:
    return list(session.scalars(select(Event).where(Event.user_id == user_id, Event.deleted_at.is_(None), Event.event_date >= now.date()).order_by(Event.event_date, Event.event_time).limit(limit)))


def month_events(session: Session, user_id: int, year: int, month: int) -> list[Event]:
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    return list(session.scalars(select(Event).where(Event.user_id == user_id, Event.deleted_at.is_(None), Event.event_date.between(start, end)).order_by(Event.event_date, Event.event_time)))


def add_expense(session: Session, event_id: int, amount_rub: int) -> Expense:
    if amount_rub < 0:
        raise ValueError("Сумма не может быть отрицательной")
    if not session.get(Event, event_id):
        raise ValueError("Событие не найдено")
    expense = Expense(event_id=event_id, amount_rub=amount_rub)
    session.add(expense)
    session.commit()
    return expense


def set_game_score(session: Session, event_id: int, score: str) -> Event:
    event = session.get(Event, event_id)
    if not event:
        raise ValueError("Событие не найдено")
    home, away = parse_score(score)
    own_goals = home if event.home_away == HomeAway.HOME else away
    opp_goals = away if event.home_away == HomeAway.HOME else home
    event.score = f"{home}:{away}"
    event.result = GameResult.WIN if own_goals > opp_goals else GameResult.LOSS
    event.status = EventStatus.WIN if event.result == GameResult.WIN else EventStatus.LOSS
    session.commit()
    return event


def total_expenses(session: Session, event_id: int) -> int:
    return session.scalar(select(func.coalesce(func.sum(Expense.amount_rub), 0)).where(Expense.event_id == event_id)) or 0


def set_attendance(session: Session, event_id: int, attendance: AttendanceStatus) -> Event:
    event = session.get(Event, event_id)
    if not event:
        raise ValueError("Событие не найдено")
    event.attendance = attendance
    session.commit()
    return event


def set_participation(session: Session, event_id: int, participation: GameParticipation) -> Event:
    event = session.get(Event, event_id)
    if not event:
        raise ValueError("Событие не найдено")
    event.participation = participation
    if participation == GameParticipation.NO:
        event.status = EventStatus.DO_NOT_PARTICIPATE
    session.commit()
    return event


def update_event_fields(session: Session, event_id: int, **fields) -> Event:
    event = session.get(Event, event_id)
    if not event:
        raise ValueError("Событие не найдено")
    for key, value in fields.items():
        if hasattr(event, key):
            setattr(event, key, value)
    _snapshot(session, event)
    session.commit()
    return event
