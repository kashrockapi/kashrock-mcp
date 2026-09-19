"""Player identity/stats, rankings, and research tools."""

from __future__ import annotations

from typing import Any, Dict

from kashrock_mcp.http import api_get, fail, ok


def register_players(mcp: Any) -> None:
    @mcp.tool()
    async def get_player(
        sport: str,
        player_id: str = "",
        q: str = "",
        view: str = "profile",
        recent_limit: int = 20,
        limit: int = 25,
    ) -> Any:
        """Find or fetch one player. Use q to resolve a nickname to a kr_pl_* id; use
        view once you have player_id. For a leaderboard of many players use
        get_rankings; for career prop performance use get_research(mode="player").

        Params:
          sport (str, e.g. "cs2"): required.
          player_id (str, e.g. "kr_pl_12345"): kr_pl_* id (preferred) or nickname.
            Required unless q is set.
          q (str, e.g. "s1mple"): nickname search — when set, ignores player_id/view
            and returns matching players instead.
          view (str, e.g. "profile"): profile (default) | stats (canonical KPR etc.) |
            stats_full (period + foundation + recent maps). Ignored when q is set.
          recent_limit (int, e.g. 20): view=stats_full only — recent maps to include, max 100.
          limit (int, e.g. 25): q search only — row cap, max 200.

        Returns:
          q set            -> {players:[...]} search hits, each with player_id.
          view=profile     -> player profile object.
          view=stats       -> canonical stats object (KPR and related).
          view=stats_full  -> {period, foundation, recent_maps}.
        Sandbox=CS2 for profile/stats; stats_full needs Hobby+.
        """
        if q:
            data = await api_get(
                f"/v6/esports/{sport}/players/search",
                {"q": q, "limit": max(1, min(int(limit or 25), 200))},
            )
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            return ok(data, sport=sport, filters={"q": q, "limit": limit})

        v = (view or "profile").strip().lower()

        if v == "stats":
            data = await api_get(f"/v6/esports/{sport}/players/{player_id}/stats")
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            return ok(data, sport=sport)

        if v == "stats_full":
            pid = str(player_id).strip()
            if not pid.isdigit():
                found = await api_get(
                    f"/v6/esports/{sport}/players/search",
                    {"q": pid, "limit": 5},
                )
                if isinstance(found, dict) and found.get("ok") is False:
                    return found
                rows = list((found or {}).get("players") or []) if isinstance(found, dict) else []
                if not rows:
                    return ok(
                        {"player": None, "note": f"No player matched '{player_id}'."},
                        sport=sport,
                    )
                pid = str(rows[0].get("player_id") or "")
                if not pid:
                    return ok(
                        {"player": rows[0], "note": "Search hit had no player_id."},
                        sport=sport,
                    )
            data = await api_get(
                f"/v6/esports/{sport}/players/{pid}/stats/full",
                {"recent_limit": max(1, min(int(recent_limit or 20), 100))},
            )
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            return ok(
                data,
                sport=sport,
                filters={"player_id": pid, "recent_limit": recent_limit},
            )

        # profile (default)
        data = await api_get(f"/v6/esports/{sport}/players/{player_id}")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport)

    @mcp.tool()
    async def get_rankings(sport: str, filter: str = "lifetime") -> Any:
        """Player rankings leaderboard for a sport — a list of many players, not a
        single-player lookup (use get_player for that).

        Params:
          sport (str, e.g. "cs2"): required.
          filter (str, e.g. "lifetime"): lifetime | last_3_months.

        Returns: {rankings:[...]} ordered leaderboard rows.
        Sandbox=CS2.
        """
        data = await api_get(
            f"/v6/esports/{sport}/rankings",
            {"filter": filter} if filter else None,
        )
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"filter": filter})

    @mcp.tool()
    async def get_research(
        sport: str = "cs2",
        mode: str = "board",
        player: str = "",
        market: str = "kills_maps_1_2",
        recent: int = 0,
    ) -> Any:
        """Research slips, board quote tapes, or one player's career tape. Distinct
        from get_lines_history, which is mechanical opening/closing prints, not
        research commentary.

        Params:
          sport (str, e.g. "cs2"): default cs2.
          mode (str, e.g. "board"): board (default, research slips for the current
            board) | board_tapes (quote tapes for the board) | player (career tape for
            one player+market).
          player (str, e.g. "kr_pl_12345"): mode=player only — kr_pl_* id (preferred),
            catalog slug, or nickname. Required for mode=player.
          market (str, e.g. "kills_maps_1_2"): mode=player only — market key.
          recent (int, e.g. 10): mode=board/player only — cap recent items; 0 = no cap.

        Returns:
          board       -> {slips:[...]} research slips.
          board_tapes -> {tapes:[...]} quote tapes.
          player      -> {tape:[...]} career tape (empty tape is 200, not 404).
        Hobby+.
        """
        m = (mode or "board").strip().lower()

        if m == "board_tapes":
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

        if m == "player":
            if not player:
                return fail("player is required for mode=player.", status=400)
            params: Dict[str, Any] = {"player": player, "sport": sport, "market": market}
            if recent:
                params["recent"] = recent
            data = await api_get("/v6/esports/research/player", params)
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            return ok(data, sport=sport, filters={"player": player, "market": market})

        # board (default)
        params = {"sport": sport}
        if recent:
            params["recent"] = recent
        data = await api_get("/v6/esports/research/board", params)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport)
