from __future__ import annotations

from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from hockey_bot.models.enums import AttendanceStatus, EventType, GameParticipation, GameResult
from hockey_bot.models.tables import Event, Expense


def _events(session: Session, user_id: int, start: date | None = None, end: date | None = None, **filters):
    stmt = select(Event).where(Event.user_id == user_id, Event.deleted_at.is_(None))
    if start and end:
        stmt = stmt.where(Event.event_date.between(start, end))
    for field, value in filters.items():
        if value is not None:
            stmt = stmt.where(getattr(Event, field) == value)
    return list(session.scalars(stmt))


def expenses_for_events(session: Session, events: list[Event]) -> int:
    ids = [e.id for e in events]
    if not ids:
        return 0
    return sum(session.scalars(select(Expense.amount_rub).where(Expense.event_id.in_(ids))))


def sports_stats(session: Session, user_id: int, **filters) -> dict[str, int | float]:
    events = _events(session, user_id, **filters)
    trainings = [e for e in events if e.event_type in {EventType.TRAINING, EventType.SCRIMMAGE}]
    games = [e for e in events if e.event_type in {EventType.GAME, EventType.AWAY_GAME}]
    wins = sum(e.result == GameResult.WIN for e in games)
    losses = sum(e.result == GameResult.LOSS for e in games)
    decided = wins + losses
    return {
        "training_count": len(trainings),
        "present": sum(e.attendance == AttendanceStatus.PRESENT for e in trainings),
        "absent": sum(e.attendance == AttendanceStatus.ABSENT for e in trainings),
        "unknown": sum(e.attendance == AttendanceStatus.UNKNOWN for e in trainings),
        "not_marked": sum(e.attendance == AttendanceStatus.NOT_MARKED for e in trainings),
        "game_count": len(games),
        "wins": wins,
        "losses": losses,
        "not_participated": sum(e.participation == GameParticipation.NO for e in games),
        "result_not_specified": sum(e.result == GameResult.NOT_SPECIFIED for e in games),
        "win_rate": round(wins / decided * 100, 1) if decided else 0,
        "expenses": expenses_for_events(session, events),
    }


def finance_month(session: Session, user_id: int, start: date, end: date) -> dict[str, int]:
    events = _events(session, user_id, start, end)
    game_events = [e for e in events if e.event_type in {EventType.GAME, EventType.AWAY_GAME}]
    training_events = [e for e in events if e.event_type in {EventType.TRAINING, EventType.SCRIMMAGE}]
    games = expenses_for_events(session, game_events)
    trainings = expenses_for_events(session, training_events)
    return {"games": games, "trainings": trainings, "total": games + trainings}
