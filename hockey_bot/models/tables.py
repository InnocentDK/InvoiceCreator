from datetime import date, datetime, time
from typing import Optional
from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, Time, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hockey_bot.db.session import Base
from hockey_bot.models.enums import AttendanceStatus, EventStatus, EventType, GameParticipation, GameResult, HomeAway, NotificationKind, RecurrenceRule


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(unique=True, index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    current_own_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=True)


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)


class OwnTeamHistory(Base):
    __tablename__ = "own_team_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class League(Base):
    __tablename__ = "leagues"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)


class LeagueTeam(Base):
    __tablename__ = "league_teams"
    __table_args__ = (UniqueConstraint("league_id", "team_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))


class Arena(Base):
    __tablename__ = "arenas"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    address: Mapped[str] = mapped_column(Text, default="")
    archived: Mapped[bool] = mapped_column(Boolean, default=False)


class Season(Base):
    __tablename__ = "seasons"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)


class EventRecurrence(Base):
    __tablename__ = "event_recurrences"
    id: Mapped[int] = mapped_column(primary_key=True)
    rule: Mapped[RecurrenceRule] = mapped_column(Enum(RecurrenceRule), default=RecurrenceRule.NONE)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), index=True)
    event_date: Mapped[date] = mapped_column(Date, index=True)
    event_time: Mapped[time] = mapped_column(Time)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), nullable=True)
    opponent_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=True)
    own_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=True)
    arena_id: Mapped[int] = mapped_column(ForeignKey("arenas.id"), nullable=True)
    home_away: Mapped[HomeAway] = mapped_column(Enum(HomeAway), nullable=True)
    cost_rub: Mapped[int] = mapped_column(Integer, default=0)
    attendance: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus), default=AttendanceStatus.NOT_MARKED)
    participation: Mapped[GameParticipation] = mapped_column(Enum(GameParticipation), default=GameParticipation.NOT_MARKED)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.PLANNED)
    result: Mapped[GameResult] = mapped_column(Enum(GameResult), default=GameResult.NOT_SPECIFIED)
    score: Mapped[str] = mapped_column(String(16), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    recurrence_id: Mapped[int] = mapped_column(ForeignKey("event_recurrences.id"), nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, index=True)
    league_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=True)
    own_team_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=True)
    opponent_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=True)
    arena_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=True)
    arena_address_snapshot: Mapped[str] = mapped_column(Text, nullable=True)
    season_name_snapshot: Mapped[str] = mapped_column(String(64), nullable=True)


class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    amount_rub: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    kind: Mapped[NotificationKind] = mapped_column(Enum(NotificationKind))
    scheduled_at_utc: Mapped[datetime] = mapped_column(DateTime, index=True)
    sent_at_utc: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    error: Mapped[str] = mapped_column(Text, nullable=True)
