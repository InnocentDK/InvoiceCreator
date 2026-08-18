from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str):
    args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    kwargs = {"poolclass": StaticPool} if database_url == "sqlite:///:memory:" else {}
    return create_engine(database_url, connect_args=args, future=True, **kwargs)


def make_session_factory(database_url: str):
    return sessionmaker(bind=make_engine(database_url), autoflush=False, expire_on_commit=False, future=True)
