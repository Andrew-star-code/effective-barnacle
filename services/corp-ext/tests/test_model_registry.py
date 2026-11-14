from __future__ import annotations

import sys
from pathlib import Path

from app.core import model_registry
from app.core.db import CORP_SCHEMA

MODULES_DIR = Path(__file__).resolve().parents[1] / "app" / "modules"


def test_every_module_models_file_is_registered() -> None:
    """Модели модуля, не импортированные в реестре, не попадут в миграции Alembic."""
    missing = [
        f"app.modules.{path.parent.name}.models"
        for path in sorted(MODULES_DIR.glob("*/models.py"))
        if f"app.modules.{path.parent.name}.models" not in sys.modules
    ]
    assert not missing, f"добавьте импорт в app/core/model_registry.py: {missing}"


def test_all_tables_live_in_corp_schema() -> None:
    tables = model_registry.metadata.tables.values()
    assert tables, "реестр пуст"
    assert {table.schema for table in tables} == {CORP_SCHEMA}
