"""HTTP client + response envelope for the KashRock API."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx

from kashrock_mcp.creds import load_key

DEFAULT_API = os.environ.get("KASHROCK_API_URL", "https://kashrock.up.railway.app").rstrip("/")
NEED_LOGIN = "Not signed in. Call the login tool — it opens Google in the browser."
UPGRADE_URL = "https://www.kashrock.com/pricing"

_PLAN_RE = re.compile(
    r"(Hobby|Builder|Pro|Sandbox)\s+plan",
    re.IGNORECASE,
)


def ok(
    data: Any,
    *,
    plan: Optional[str] = None,
    total: Optional[int] = None,
    returned: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
    hint: Optional[str] = None,
    **extra: Any,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {"ok": True, "data": data}
    if plan is not None:
        out["plan"] = plan
    if total is not None:
        out["total"] = total
    if returned is not None:
        out["returned"] = returned
    if filters:
        out["filters"] = {k: v for k, v in filters.items() if v not in (None, "")}
    if hint:
        out["hint"] = hint
    out.update(extra)
    return out


def fail(
    message: Any,
    *,
    status: Optional[int] = None,
    required_plan: Optional[str] = None,
    your_plan: Optional[str] = None,
) -> Dict[str, Any]:
    detail = message
    if isinstance(message, dict):
        detail = message.get("detail") or message
    text = detail if isinstance(detail, str) else json.dumps(detail)
    if not required_plan and isinstance(text, str):
        match = _PLAN_RE.search(text)
        if match:
            required_plan = match.group(1).lower()
    out: Dict[str, Any] = {
        "ok": False,
        "error": "plan_required" if status == 403 and required_plan else "request_failed",
        "message": text,
        "upgrade_url": UPGRADE_URL,
    }
    if status is not None:
        out["status"] = status
    if required_plan:
        out["required_plan"] = required_plan
    if your_plan:
        out["your_plan"] = your_plan
    return out


async def api_get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    key = load_key()
    if not key:
        return fail(NEED_LOGIN, status=401)
    clean = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    query = f"?{urlencode(clean)}" if clean else ""
    url = f"{DEFAULT_API}{path}{query}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, headers={"X-API-Key": key})
    try:
        body = response.json()
    except json.JSONDecodeError:
        body = {"detail": response.text[:500]}
    if response.status_code >= 400:
        return fail(body, status=response.status_code)
    return body


async def api_post(path: str, payload: Dict[str, Any]) -> Any:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{DEFAULT_API}{path}", json=payload)
    try:
        return response.status_code, response.json()
    except json.JSONDecodeError:
        return response.status_code, {"detail": response.text[:500]}
