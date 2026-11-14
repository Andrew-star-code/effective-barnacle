from __future__ import annotations

from collections.abc import Iterator

import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _isolated_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[None]:
    """Тесты не читают config/corp-ext.yaml разработчика и переменные его окружения."""
    monkeypatch.setenv("CORP_EXT_CONFIG", str(tmp_path_factory.mktemp("cfg") / "absent.yaml"))
    monkeypatch.setenv("CORP_EXT_ENV", "test")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
