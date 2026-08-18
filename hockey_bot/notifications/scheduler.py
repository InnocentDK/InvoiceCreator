from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from hockey_bot.models.enums import NotificationKind
from hockey_bot.models.tables import Event, Notification, User


def local_event_dt(event: Event, user: User) -> datetime:
    return datetime.combine(event.event_date, event.event_time, tzinfo=ZoneInfo(user.timezone))


def planned_notifications(event: Event, user: User, now_utc: datetime | None = None) -> list[tuple[NotificationKind, datetime]]:
    now_utc = now_utc or datetime.utcnow()
    event_dt = local_event_dt(event, user)
    day_before = datetime.combine(event.event_date - timedelta(days=1), time(12, 0), tzinfo=ZoneInfo(user.timezone))
    candidates = [(NotificationKind.DAY_BEFORE, day_before), (NotificationKind.THREE_HOURS, event_dt - timedelta(hours=3))]
    return [(k, dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)) for k, dt in candidates if dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None) > now_utc]


def ensure_notifications(session: Session, event: Event, user: User) -> list[Notification]:
    result = []
    for kind, when in planned_notifications(event, user):
        n = Notification(event_id=event.id, kind=kind, scheduled_at_utc=when)
        session.add(n)
        result.append(n)
    session.commit()
    return result
