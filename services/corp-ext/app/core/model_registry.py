"""Единая точка регистрации таблиц схемы ``corp``.

Alembic видит только те таблицы, чьи модули импортированы до чтения ``Base.metadata``.
Новый ``app/modules/<имя>/models.py`` добавляется сюда отдельной строкой импорта;
тест ``tests/test_model_registry.py`` падает, если это забыто.
"""

from __future__ import annotations

from app.core import models as _core_models  # noqa: F401  (регистрация таблиц)
from app.core.db import Base

metadata = Base.metadata
