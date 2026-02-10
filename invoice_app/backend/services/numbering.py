from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Invoice


def get_next_invoice_number(db: Session) -> str:
    """Return next invoice number in 3-digit format."""
    max_number = db.scalar(select(func.max(Invoice.number)))
    if not max_number:
        return "001"
    try:
        next_number = int(max_number) + 1
    except ValueError:
        next_number = 1
    return f"{next_number:03d}"
