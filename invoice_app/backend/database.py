from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Organization

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "invoice_app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    seed_organizations()


def seed_organizations() -> None:
    default_organizations = [
        {
            "name": "ИП Иванов И.И.",
            "inn": "770123456789",
            "kpp": "",
            "address": "г. Москва, ул. Примерная, д. 1",
            "bank": "ПАО Сбербанк",
            "account": "40802810900000000001",
            "bik": "044525225",
        },
        {
            "name": "ООО Патент Консалт",
            "inn": "7701234567",
            "kpp": "770101001",
            "address": "г. Москва, ул. Правовая, д. 10",
            "bank": "АО Альфа-Банк",
            "account": "40702810123450000002",
            "bik": "044525593",
        },
    ]

    with SessionLocal() as session:
        exists = session.scalar(select(Organization.id).limit(1))
        if exists:
            return
        for org_data in default_organizations:
            session.add(Organization(**org_data))
        session.commit()
