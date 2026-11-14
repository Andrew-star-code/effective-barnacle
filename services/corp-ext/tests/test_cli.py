from __future__ import annotations

import json

import pytest

from app.cli.__main__ import main


def test_openapi_dump(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["openapi"]) == 0
    spec = json.loads(capsys.readouterr().out)
    assert "/health" in spec["paths"]


def test_config_check_ok(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["config", "check"]) == 0
    assert "корректна" in capsys.readouterr().out
