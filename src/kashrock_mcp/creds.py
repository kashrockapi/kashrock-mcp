"""Local API key store (~/.kashrock/credentials)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

DIR = Path.home() / ".kashrock"
PATH = DIR / "credentials"


def load_credentials() -> Dict[str, Any]:
    env = os.environ.get("KASHROCK_API_KEY", "").strip()
    data = _read()
    if env:
        return {**data, "api_key": env, "from_env": True}
    return data


def load_key() -> Optional[str]:
    data = load_credentials()
    key = str(data.get("api_key") or "").strip()
    return key or None


def save_credentials(api_key: str, email: str | None, plan: str | None) -> None:
    DIR.mkdir(mode=0o700, exist_ok=True)
    payload = {"api_key": api_key, "email": email or "", "plan": plan or ""}
    PATH.write_text(json.dumps(payload), encoding="utf-8")
    PATH.chmod(0o600)


def describe() -> str:
    env = os.environ.get("KASHROCK_API_KEY", "").strip()
    if env:
        return "Using KASHROCK_API_KEY from the environment."
    data = _read()
    email = data.get("email") or "signed in"
    if data.get("api_key"):
        return f"Signed in as {email}."
    return "Not signed in."


def _read() -> Dict[str, Any]:
    if not PATH.is_file():
        return {}
    try:
        data = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}
