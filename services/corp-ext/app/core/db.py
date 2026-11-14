"""Доступ к Postgres: только схема ``corp``.

Таблицы WeKnora читаются исключительно через ``app.modules.weknora`` под ролью
с правом SELECT; писать в них нельзя (исключения — SPEC §16.2).
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import DatabaseSettings

CORP_SCHEMA = "corp"

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(schema=CORP_SCHEMA, naming_convention=NAMING_CONVENTION)


def create_engine(settings: DatabaseSettings) -> AsyncEngine:
    return create_async_engine(settings.dsn, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker:  # type: ignore[type-arg]
    return async_sessionmaker(engine, expire_on_commit=False)
