#!/usr/bin/env python3
"""Проверки документации (SPEC §19.4). Только стандартная библиотека.

1. У каждого модуля corp-ext есть README.md.
2. Относительные ссылки в Markdown-файлах проекта ведут на существующие файлы.
3. Каждый коммит ``P-NN:`` в подмодуле weknora есть в docs/patches.md.

Проверка актуальности сгенерированного API-клиента — ``make gen-api-check``.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"weknora", "node_modules", ".venv", "dist", ".git"}
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
PATCH_RE = re.compile(r"^(P-\d{2}):")


def markdown_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*.md")
        if not SKIP_DIRS.intersection(path.relative_to(ROOT).parts)
    ]


def check_module_readmes() -> list[str]:
    modules = ROOT / "services" / "corp-ext" / "app" / "modules"
    return [
        f"нет README.md у модуля {module.relative_to(ROOT).as_posix()}"
        for module in sorted(modules.iterdir())
        if module.is_dir() and module.name != "__pycache__" and not (module / "README.md").is_file()
    ]


def check_links() -> list[str]:
    errors = []
    for path in markdown_files():
        text = CODE_RE.sub("", path.read_text(encoding="utf-8"))
        for target in LINK_RE.findall(text):
            target = target.strip("<>")
            if re.match(r"[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue
            file_part = target.split("#", 1)[0]
            if not (path.parent / file_part).exists():
                errors.append(f"{path.relative_to(ROOT).as_posix()}: битая ссылка {target}")
    return errors


def check_patch_registry() -> list[str]:
    submodule = ROOT / "weknora"
    if not (submodule / ".git").exists():
        return []
    result = subprocess.run(  # noqa: S603
        ["git", "-C", str(submodule), "log", "--format=%s", "-E", "--grep=^P-[0-9]{2}:"],  # noqa: S607
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        return [f"не удалось прочитать историю подмодуля weknora: {result.stderr.strip()}"]
    registry = (ROOT / "docs" / "patches.md").read_text(encoding="utf-8")
    patches = {m.group(1) for line in result.stdout.splitlines() if (m := PATCH_RE.match(line))}
    return [
        f"коммит {patch} есть в подмодуле weknora, но не отмечен в docs/patches.md как применённый"
        for patch in sorted(patches)
        if not re.search(rf"\|\s*{patch}\s*\|[^\n]*\|\s*(применён|в PR|принят)", registry)
    ]


def main() -> int:
    errors = check_module_readmes() + check_links() + check_patch_registry()
    for error in errors:
        print(f"docs-check: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"docs-check: OK ({len(markdown_files())} файлов Markdown)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
