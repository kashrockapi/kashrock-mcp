"""Register all MCP tool modules."""

from __future__ import annotations

from typing import Any

from kashrock_mcp.tools_board import register_board
from kashrock_mcp.tools_history import register_history
from kashrock_mcp.tools_live import register_live
from kashrock_mcp.tools_match_intel import register_match_intel
from kashrock_mcp.tools_players import register_players
from kashrock_mcp.tools_schedule import register_schedule
from kashrock_mcp.tools_session import register_session


def register_tools(mcp: Any) -> None:
    register_session(mcp)
    register_board(mcp)
    register_players(mcp)
    register_schedule(mcp)
    register_live(mcp)
    register_history(mcp)
    register_match_intel(mcp)
