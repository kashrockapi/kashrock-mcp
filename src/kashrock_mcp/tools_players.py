"""Players, rankings, and research tools."""

from __future__ import annotations

from typing import Any, Dict

from kashrock_mcp.http import api_get, ok


def register_players(mcp: Any) -> None:
    @mcp.tool()
    async def search_players(sport: str, q: str, limit: int = 25) -> Any:
        """Find a player by nickname. Returns kr_pl_* ids. limit caps rows (default 25, max 200)."""
        data = await api_get(
            f"/v6/esports/{sport}/players/search",
            {"q": q, "limit": max(1, min(int(limit or 25), 200))},
        )
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"q": q, "limit": limit})

    @mcp.tool()
    async def get_player(sport: str, player_id: str) -> Any:
        """Player profile. player_id is kr_pl_* (preferred) or nickname."""
        data = await api_get(f"/v6/esports/{sport}/players/{player_id}")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport)

    @mcp.tool()
    async def get_player_stats(sport: str, player_id: str) -> Any:
        """Canonical player stats (KPR and related)."""
        data = await api_get(f"/v6/esports/{sport}/players/{player_id}/stats")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport)

    @mcp.tool()
    async def get_player_stats_full(
        sport: str,
        player: str,
        recent_limit: int = 20,
    ) -> Any:
        """Full Redis aggregate: period stats + foundation + recent maps. player = nickname or kr_pl_* id."""
        player_id = str(player).strip()
        if not player_id.isdigit():
            found = await api_get(
                f"/v6/esports/{sport}/players/search",
                {"q": player_id, "limit": 5},
            )
            if isinstance(found, dict) and found.get("ok") is False:
                return found
            rows = list((found or {}).get("players") or []) if isinstance(found, dict) else []
            if not rows:
                return ok(
                    {"player": None, "note": f"No player matched '{player}'."},
                    sport=sport,
                )
            player_id = str(rows[0].get("player_id") or "")
            if not player_id:
                return ok(
                    {"player": rows[0], "note": "Search hit had no player_id."},
                    sport=sport,
                )
        data = await api_get(
            f"/v6/esports/{sport}/players/{player_id}/stats/full",
            {"recent_limit": max(1, min(int(recent_limit or 20), 100))},
        )
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(
            data,
            sport=sport,
            filters={"player_id": player_id, "recent_limit": recent_limit},
        )

    @mcp.tool()
    async def get_rankings(sport: str, filter: str = "lifetime") -> Any:
        """Player rankings. filter: lifetime | last_3_months."""
        data = await api_get(
            f"/v6/esports/{sport}/rankings",
            {"filter": filter} if filter else None,
        )
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"filter": filter})

    @mcp.tool()
    async def research_board(sport: str = "cs2", recent: int = 0) -> Any:
        """Research slips for the current board."""
        params: Dict[str, Any] = {"sport": sport}
        if recent:
            params["recent"] = recent
        data = await api_get("/v6/esports/research/board", params)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport)

    @mcp.tool()
    async def research_board_tapes(sport: str = "cs2") -> Any:
        """Research quote tapes for the current board (Hobby+)."""
        data = await api_get("/v6/esports/research/board-tapes", {"sport": sport})
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        tapes = list((data or {}).get("tapes") or []) if isinstance(data, dict) else []
        return ok(
            data,
            sport=sport,
            total=(data or {}).get("count") if isinstance(data, dict) else len(tapes),
            returned=len(tapes),
        )

    @mcp.tool()
    async def research_player(
        player: str,
        sport: str = "cs2",
        market: str = "kills_maps_1_2",
        recent: int = 0,
    ) -> Any:
        """Career tape for one player and market. player is kr_pl_* (preferred), catalog slug, or nickname. Empty tape is 200, not 404."""
        params: Dict[str, Any] = {
            "player": player,
            "sport": sport,
            "market": market,
        }
        if recent:
            params["recent"] = recent
        data = await api_get("/v6/esports/research/player", params)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"player": player, "market": market})
