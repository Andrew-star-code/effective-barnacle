"""MCP-сервер data-gateway: инструменты для модели (SPEC §10.5).

Этап 0 — только каркас: один служебный инструмент `gateway_status`, чтобы проверить связку
WeKnora → MCP. Каталог наборов данных, функции и SQL — этап 9.
"""

from pathlib import Path
from typing import TypedDict

from mcp.server.mcpserver import MCPServer

SERVICE_VERSION = "0.1.0"
CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"


class GatewayStatus(TypedDict):
    service: str
    version: str
    datasets: int
    catalog: str


def gateway_status() -> GatewayStatus:
    """Состояние семантического слоя: сколько наборов данных описано в каталоге.

    Пользовательских данных не возвращает, поэтому не требует X-Corp-User
    (подпись пользователя — P-03, этап 4).
    """
    datasets = sorted((CATALOG_DIR / "datasets").glob("*.yaml"))
    return GatewayStatus(
        service="data-gateway",
        version=SERVICE_VERSION,
        datasets=len(datasets),
        catalog="настроен" if datasets else "пуст: наборы данных появятся на этапе 9",
    )


def build_server() -> MCPServer:
    server = MCPServer(
        name="data-gateway",
        title="Корпоративные данные",
        version=SERVICE_VERSION,
        instructions=(
            "Доступ к корпоративным данным через семантический слой. "
            "Пока доступен только инструмент проверки состояния."
        ),
    )
    server.tool(
        name="gateway_status",
        title="Состояние источника корпоративных данных",
        description=(
            "Возвращает состояние сервиса корпоративных данных и число описанных наборов данных. "
            "Вызывай, когда пользователь спрашивает, доступны ли корпоративные данные."
        ),
    )(gateway_status)
    return server
