from __future__ import annotations

from enum import StrEnum


class EventType(StrEnum):
    TRAINING = "training"
    SCRIMMAGE = "scrimmage"
    GAME = "game"
    AWAY_GAME = "away_game"


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"
    NOT_MARKED = "not_marked"


class GameParticipation(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"
    NOT_MARKED = "not_marked"


class GameResult(StrEnum):
    WIN = "win"
    LOSS = "loss"
    NOT_SPECIFIED = "not_specified"


class EventStatus(StrEnum):
    PLANNED = "planned"
    WIN = "win"
    LOSS = "loss"
    CANCELLED = "cancelled"
    DO_NOT_PARTICIPATE = "do_not_participate"
    RESULT_NOT_SPECIFIED = "result_not_specified"


class HomeAway(StrEnum):
    HOME = "home"
    AWAY = "away"


class RecurrenceRule(StrEnum):
    NONE = "none"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class NotificationKind(StrEnum):
    DAY_BEFORE = "day_before"
    THREE_HOURS = "three_hours"
    EIGHT_HOURS = "eight_hours"


RU_LABELS = {
    EventType.TRAINING: "🏒 Тренировка",
    EventType.SCRIMMAGE: "🏒 Двухсторонка",
    EventType.GAME: "🏆 Игра",
    EventType.AWAY_GAME: "🚌 Выездная игра",
    AttendanceStatus.PRESENT: "Присутствовал",
    AttendanceStatus.ABSENT: "Отсутствовал",
    AttendanceStatus.UNKNOWN: "Не знаю",
    AttendanceStatus.NOT_MARKED: "Не отметился",
    GameParticipation.YES: "Участвую",
    GameParticipation.NO: "Не участвовать",
    GameParticipation.UNKNOWN: "Пока не знаю",
    GameParticipation.NOT_MARKED: "Не отметился",
    GameResult.WIN: "Победа",
    GameResult.LOSS: "Поражение",
    GameResult.NOT_SPECIFIED: "Результат не указан",
    HomeAway.HOME: "Дома",
    HomeAway.AWAY: "На выезде",
}
