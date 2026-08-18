from __future__ import annotations

from datetime import date, datetime, time


def parse_ru_date(value: str) -> date:
    try:
        return datetime.strptime(value.strip(), "%d.%m.%Y").date()
    except ValueError as exc:
        raise ValueError("Введите дату в формате ДД.ММ.ГГГГ") from exc


def parse_time(value: str) -> time:
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except ValueError as exc:
        raise ValueError("Введите время в формате ЧЧ:ММ") from exc


def parse_non_negative_amount(value: str) -> int:
    try:
        amount = int(value.strip())
    except ValueError as exc:
        raise ValueError("Введите сумму числом без ₽") from exc
    if amount < 0:
        raise ValueError("Сумма не может быть отрицательной")
    return amount


def parse_score(value: str) -> tuple[int, int]:
    parts = value.strip().split(":")
    if len(parts) != 2:
        raise ValueError("Введите счёт в формате Хозяева:Гости")
    try:
        home, away = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ValueError("Счёт должен содержать только числа") from exc
    if home < 0 or away < 0:
        raise ValueError("Счёт не может быть отрицательным")
    if home == away:
        raise ValueError("Ничьи в первой версии не поддерживаются")
    return home, away
