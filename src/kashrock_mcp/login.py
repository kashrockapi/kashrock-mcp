"""Open Google in the browser and wait for the live API key."""

from __future__ import annotations

import asyncio
import time
import webbrowser

from kashrock_mcp.creds import describe, load_key, save_credentials
from kashrock_mcp.http import api_post


async def run_login() -> str:
    if load_key():
        return describe() + " Already have a key — skip login unless it is rejected."

    status, started = await api_post("/v1/dev/mcp/device/start", {})
    if status >= 400 or not isinstance(started, dict) or "device_code" not in started:
        return f"Could not start Google login: {started}"

    verify_url = started["verify_url"]
    webbrowser.open(verify_url)
    interval = max(int(started.get("interval") or 2), 1)
    deadline = time.monotonic() + int(started.get("expires_in") or 600)

    while time.monotonic() < deadline:
        await asyncio.sleep(interval)
        poll_status, body = await api_post(
            "/v1/dev/mcp/device/poll",
            {"device_code": started["device_code"]},
        )
        if poll_status >= 400:
            return f"Login poll failed: {body}"
        state = body.get("status")
        if state == "pending":
            continue
        if state == "expired":
            return "Sign-in expired. Call login again."
        if state == "ready" and body.get("api_key"):
            save_credentials(body["api_key"], body.get("email"), body.get("plan"))
            email = body.get("email") or "your Google account"
            return f"Signed in as {email} (plan: {body.get('plan') or 'unknown'}). Call whoami, then get_props / get_lines / get_moneylines."
        return f"Unexpected login state: {body}"

    return f"Timed out waiting for Google. Open this URL and try login again: {verify_url}"
