"""Installed MCP version + PyPI latest (update nag for whoami)."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any, Dict, Optional

import httpx

PACKAGE = "kashrock-mcp"
PYPI_JSON = f"https://pypi.org/pypi/{PACKAGE}/json"
REFRESH_HINT = (
    "MCP update available — restart the KashRock MCP "
    "(or run: uvx --refresh kashrock-mcp)."
)


def installed_version() -> str:
    try:
        return version(PACKAGE)
    except PackageNotFoundError:
        # Editable / source checkout before install metadata exists.
        return "0.6.5"


async def fetch_pypi_latest(timeout: float = 4.0) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(PYPI_JSON)
            response.raise_for_status()
            data = response.json()
    except Exception:
        return None
    info = data.get("info") if isinstance(data, dict) else None
    if not isinstance(info, dict):
        return None
    latest = info.get("version")
    return str(latest) if latest else None


def _tuple(ver: str) -> tuple:
    parts = []
    for bit in str(ver).split("."):
        try:
            parts.append(int(bit))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def is_outdated(current: str, latest: Optional[str]) -> bool:
    if not latest:
        return False
    return _tuple(current) < _tuple(latest)


async def version_payload() -> Dict[str, Any]:
    current = installed_version()
    latest = await fetch_pypi_latest()
    outdated = is_outdated(current, latest)
    out: Dict[str, Any] = {
        "mcp_version": current,
        "mcp_latest": latest,
        "mcp_outdated": outdated,
    }
    if outdated:
        out["mcp_update"] = REFRESH_HINT
    return out
