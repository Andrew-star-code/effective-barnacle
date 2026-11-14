"""Конфигурация corp-ext.

Источники по убыванию приоритета: переменные окружения ``CORP_EXT_*``
(вложенность через ``__``), затем YAML-файл из ``CORP_EXT_CONFIG``
(по умолчанию ``config/corp-ext.yaml``). Секреты в YAML не кладутся (SPEC §6.3):
только переменные окружения или ``*_file``.

Конфиг валидируется при старте; при ошибке сервис не запускается и печатает
сообщение вида ``ldap.urls: не задан ни один контроллер домена`` (SPEC §18.4).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

DEFAULT_CONFIG_PATH = "config/corp-ext.yaml"


class ConfigError(RuntimeError):
    """Ошибка конфигурации с сообщением, понятным без трассировки."""


class LogSettings(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    json_output: bool = Field(
        default=True, description="JSON в stdout; false — читаемый вывод для dev"
    )


class DatabaseSettings(BaseModel):
    dsn: str = Field(
        default="postgresql+asyncpg://corp_ext@postgres:5432/weknora",
        description="DSN Postgres; пароль — через CORP_EXT_DATABASE__DSN, не в YAML",
    )
    db_schema: str = Field(default="corp", description="Своя схема; в таблицы WeKnora не пишем")


class RedisSettings(BaseModel):
    url: str = Field(default="redis://redis:6379/5", description="Отдельный номер БД от WeKnora")


class PerIpRule(BaseModel):
    max_failures: int = 20
    window_minutes: int = 15
    lock_minutes: int = 60


class AuthSettings(BaseModel):
    bootstrap_admins: list[str] = Field(default_factory=list, description="Логины первых админов")
    access_group: str = Field(default="", description="Пусто — пускать всех включённых в домене")
    per_ip: PerIpRule = Field(default_factory=PerIpRule)


class LdapAttributes(BaseModel):
    guid: str = "objectGUID"
    login: str = "sAMAccountName"
    email: str = "mail"
    display_name: str = "displayName"
    last_name: str = "sn"
    first_name: str = "givenName"
    middle_name: str = "middleName"
    display_name_pattern: str = "{last} {first} {middle}"
    title: str = "title"
    department: str = Field(default="", description="Пусто, пока AD не отдаёт отдел (SPEC §7.6)")
    company: str = "company"
    office: str = "physicalDeliveryOfficeName"
    phone: str = "telephoneNumber"
    mobile: str = "mobile"
    manager: str = "manager"
    employee_id: str = "employeeID"
    photo: str = "thumbnailPhoto"


class LdapSettings(BaseModel):
    urls: list[str] = Field(default_factory=list)
    ca_cert_file: Path | None = None
    bind_dn: str = ""
    bind_password_file: Path | None = None
    base_dn: str = ""
    attributes: LdapAttributes = Field(default_factory=LdapAttributes)
    sync_interval_minutes: int = Field(default=60, ge=1)

    @field_validator("urls")
    @classmethod
    def _urls_not_empty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("не задан ни один контроллер домена")
        for url in value:
            if not url.startswith(("ldaps://", "ldap://")):
                raise ValueError(f"адрес должен начинаться с ldaps:// или ldap://: {url}")
        return value


class SourceToggle(BaseModel):
    enabled: bool = False


class RuleSource(SourceToggle):
    rules: list[dict[str, object]] = Field(default_factory=list)


class AdDepartmentSource(SourceToggle):
    attribute: str = "department"
    mapping_mode: Literal["explicit", "auto_create"] = "explicit"
    on_unmapped: Literal["report", "ignore"] = "report"


class AdGroupSource(SourceToggle):
    nested: bool = True


class GroupSources(BaseModel):
    manual: SourceToggle = Field(default_factory=lambda: SourceToggle(enabled=True))
    rule: RuleSource = Field(default_factory=RuleSource)
    ad_department: AdDepartmentSource = Field(default_factory=AdDepartmentSource)
    ad_group: AdGroupSource = Field(default_factory=AdGroupSource)


class GroupsSettings(BaseModel):
    default_groups: list[str] = Field(default_factory=list)
    sources: GroupSources = Field(default_factory=GroupSources)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CORP_EXT_",
        env_nested_delimiter="__",
        extra="forbid",
    )

    env: Literal["dev", "test", "prod"] = "prod"
    log: LogSettings = Field(default_factory=LogSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    # ldap обязателен с этапа 1; до появления adsync секция может отсутствовать.
    ldap: LdapSettings | None = None
    groups: GroupsSettings = Field(default_factory=GroupsSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        yaml_path = Path(os.environ.get("CORP_EXT_CONFIG", DEFAULT_CONFIG_PATH))
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file=yaml_path),
        )


def format_validation_error(exc: ValidationError) -> str:
    """``ldap.urls: не задан ни один контроллер домена`` — по строке на ошибку."""
    lines = []
    for err in exc.errors():
        location = ".".join(str(part) for part in err["loc"])
        message = err["msg"].removeprefix("Value error, ")
        lines.append(f"{location}: {message}")
    return "\n".join(lines)


def load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        raise ConfigError(format_validation_error(exc)) from exc


@lru_cache
def get_settings() -> Settings:
    return load_settings()
