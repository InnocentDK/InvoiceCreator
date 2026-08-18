from __future__ import annotations

from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from hockey_bot.models.tables import Arena, League, LeagueTeam, OwnTeamHistory, Season, Team, User


def create_named(session: Session, model, name: str, **extra):
    if not name.strip():
        raise ValueError("Название не может быть пустым")
    obj = model(name=name.strip(), **extra)
    session.add(obj)
    session.commit()
    return obj


def archive(session: Session, model, object_id: int, archived: bool = True) -> bool:
    obj = session.get(model, object_id)
    if not obj:
        return False
    obj.archived = archived
    session.commit()
    return True


def active(session: Session, model):
    return list(session.scalars(select(model).where(model.archived.is_(False)).order_by(model.name)))


def link_team_to_league(session: Session, league_id: int, team_id: int) -> LeagueTeam:
    link = session.scalar(select(LeagueTeam).where(LeagueTeam.league_id == league_id, LeagueTeam.team_id == team_id))
    if link:
        return link
    link = LeagueTeam(league_id=league_id, team_id=team_id)
    session.add(link)
    session.commit()
    return link


def set_own_team(session: Session, user: User, team_id: int) -> None:
    now = datetime.utcnow()
    session.execute(update(OwnTeamHistory).where(OwnTeamHistory.user_id == user.id, OwnTeamHistory.ended_at.is_(None)).values(ended_at=now))
    user.current_own_team_id = team_id
    session.add(OwnTeamHistory(user_id=user.id, team_id=team_id, started_at=now))
    session.commit()
