"""CLI corp-ext: ``python -m app.cli <команда>``.

Сейчас: ``config check`` и ``openapi``. Команды ``ad check``, ``provision``, ``groups``,
``create-admin``, ``purge`` появляются на этапе 1 и далее (SPEC §6.6, §7.5).
"""

from __future__ import annotations

import argparse
import json
import sys

from app.core.config import ConfigError, LogSettings, Settings, load_settings


def _cmd_config_check(_: argparse.Namespace) -> int:
    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"Ошибка конфигурации:\n{exc}", file=sys.stderr)
        return 1
    print(f"Конфигурация корректна (env={settings.env}).")
    return 0


def _cmd_openapi(_: argparse.Namespace) -> int:
    """Печатает OpenAPI без запуска сервера — для ``make gen-api``."""
    from app.main import create_app

    # Логи идут в stdout, поэтому здесь они приглушены: в stdout должен попасть только JSON.
    app = create_app(Settings(env="dev", log=LogSettings(level="ERROR")))
    json.dump(app.openapi(), sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="Команды corp-ext")
    sub = parser.add_subparsers(dest="command", required=True)

    config = sub.add_parser("config", help="работа с конфигурацией")
    config_sub = config.add_subparsers(dest="subcommand", required=True)
    config_sub.add_parser("check", help="проверить конфигурацию").set_defaults(
        func=_cmd_config_check
    )

    sub.add_parser("openapi", help="вывести OpenAPI в stdout").set_defaults(func=_cmd_openapi)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
