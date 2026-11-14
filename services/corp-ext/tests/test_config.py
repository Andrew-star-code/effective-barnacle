from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import ConfigError, load_settings


def _write(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, text: str) -> None:
    path = tmp_path / "corp-ext.yaml"
    path.write_text(text, encoding="utf-8")
    monkeypatch.setenv("CORP_EXT_CONFIG", str(path))


def test_defaults_without_file() -> None:
    settings = load_settings()
    assert settings.env == "test"
    assert settings.groups.sources.manual.enabled is True
    assert settings.groups.sources.ad_department.enabled is False
    assert settings.ldap is None


def test_yaml_and_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _write(
        monkeypatch,
        tmp_path,
        "auth:\n  bootstrap_admins: [ivanov]\nldap:\n  urls: ['ldaps://dc1.corp.local:636']\n",
    )
    monkeypatch.setenv("CORP_EXT_REDIS__URL", "redis://localhost:6379/9")
    settings = load_settings()
    assert settings.auth.bootstrap_admins == ["ivanov"]
    assert settings.ldap is not None
    assert settings.ldap.attributes.department == ""
    assert settings.redis.url == "redis://localhost:6379/9"


def test_empty_ldap_urls_gives_readable_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write(monkeypatch, tmp_path, "ldap:\n  urls: []\n")
    with pytest.raises(ConfigError) as excinfo:
        load_settings()
    assert "ldap.urls: не задан ни один контроллер домена" in str(excinfo.value)


def test_unknown_key_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _write(monkeypatch, tmp_path, "ldpa: {}\n")
    with pytest.raises(ConfigError, match="ldpa"):
        load_settings()


def test_example_config_is_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    example = Path(__file__).resolve().parents[3] / "config" / "corp-ext.example.yaml"
    monkeypatch.setenv("CORP_EXT_CONFIG", str(example))
    monkeypatch.delenv("CORP_EXT_ENV")
    assert load_settings().env == "dev"
