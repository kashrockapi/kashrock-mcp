"""History / grading-input tools. Match/player history: Sandbox=30d, Hobby=90d,
Builder+=full vault. Quote-tape history (get_history_tape/get_lines_history) stays
Builder+."""

from __future__ import annotations

from typing import Any, Dict

from kashrock_mcp.http import api_get, fail, ok


def register_history(mcp: Any) -> None:
    @mcp.tool()
    async def get_gamelogs(sport: str, player: str, limit: int = 200) -> Any:
        """Per-map player gamelogs (kills, ADR, gold, GPM, hero when present). player = slug, nickname, or kr_pl_*. Sandbox=last 30 days, Hobby=last 90 days, Builder+=full vault."""
        data = await api_get(
            f"/v6/esports/{sport}/players/{player}/gamelogs",
            {"limit": max(1, min(int(limit or 200), 5000))},
        )
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        logs = list((data or {}).get("gamelogs") or []) if isinstance(data, dict) else []
        return ok(
            data,
            sport=sport,
            total=(data or {}).get("total") if isinstance(data, dict) else len(logs),
            returned=len(logs),
            filters={"player": player, "limit": limit},
        )

    @mcp.tool()
    async def get_boxscore(sport: str, match_slug: str = "", limit: int = 20) -> Any:
        """Finished-match vault boxscore + STARTER/SUB lineup and sport-native model fields by slug or kr_match_id (or recent list). Not live KDA — use get_live_boxscore. Sandbox=last 30 days, Hobby=last 90 days, Builder+=full vault."""
        slug = (match_slug or "").strip()
        if slug and slug.lower() in {"none", "null", "undefined", "nil"}:
            return fail(
                "Invalid match_slug — use a real slug or kr_match_id from get_matches, not None/null.",
                status=400,
            )
        if slug:
            data = await api_get(f"/v6/esports/{sport}/matches/{slug}/boxscore")
        else:
            data = await api_get(
                f"/v6/esports/{sport}/boxscores",
                {"limit": max(1, min(int(limit or 20), 100))},
            )
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"match_slug": slug or None})

    @mcp.tool()
    async def get_results(sport: str, grade: str = "") -> Any:
        """Settled prop grades: hit | miss | push | pending | error. Sandbox=last 30 days, Hobby=last 90 days, Builder+=full vault."""
        params: Dict[str, Any] = {}
        if grade:
            params["grade"] = grade
        data = await api_get(f"/v6/esports/{sport}/results", params or None)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        rows = list((data or {}).get("results") or []) if isinstance(data, dict) else []
        return ok(
            data,
            sport=sport,
            total=(data or {}).get("total") if isinstance(data, dict) else len(rows),
            returned=len(rows),
            filters={"grade": grade or None},
        )

    @mcp.tool()
    async def get_lines_history(
        sport: str,
        match_id: str,
        market: str = "",
        book: str = "",
    ) -> Any:
        """Opening and closing team mainlines for a match slug or kr_match_id. Builder+. Not live in-play steam."""
        slug = (match_id or "").strip()
        if not slug or slug.lower() in {"none", "null", "undefined", "nil"}:
            return fail(
                "Invalid match_id — use slug or kr_match_id from get_matches.",
                status=400,
            )
        params: Dict[str, Any] = {}
        if market:
            params["market"] = market
        if book:
            params["book"] = book
        data = await api_get(
            f"/v6/esports/{sport}/matches/{slug}/lines/history",
            params or None,
        )
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        markets = list((data or {}).get("markets") or []) if isinstance(data, dict) else []
        return ok(
            data,
            sport=sport,
            total=len(markets),
            returned=len(markets),
            filters={"match_id": slug, "market": market or "all", "book": book or None},
            hint="Vault closing prints. In-play steam is get_live_odds_history.",
        )

    @mcp.tool()
    async def get_history_tape(
        prop_id: str = "",
        book: str = "",
        market_key: str = "",
    ) -> Any:
        """Quote tape for a prop/book or market_key. Builder+. Need market_key OR prop_id+book."""
        if not market_key and not (prop_id and book):
            return fail("Provide market_key, or prop_id and book.", status=400)
        params: Dict[str, Any] = {}
        if market_key:
            params["market_key"] = market_key
        if prop_id:
            params["prop_id"] = prop_id
        if book:
            params["book"] = book
        data = await api_get("/v6/esports/history/contract", params)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(
            data,
            filters={"prop_id": prop_id or None, "book": book or None, "market_key": market_key or None},
            hint="Tape is vault history of the line — pair with get_gamelogs to grade.",
        )

    @mcp.tool()
    async def get_team_h2h(
        sport: str,
        team1: str,
        team2: str,
        limit: int = 50,
    ) -> Any:
        """Finished team-vs-team meetings (scores + maps) from the history vault."""
        data = await api_get(
            f"/v6/esports/{sport}/teams/h2h",
            {
                "team1": team1,
                "team2": team2,
                "limit": max(1, min(int(limit or 50), 500)),
            },
        )
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        recent = list((data or {}).get("recent") or []) if isinstance(data, dict) else []
        return ok(
            data,
            sport=sport,
            total=(data or {}).get("meetings") if isinstance(data, dict) else len(recent),
            returned=len(recent),
            filters={"team1": team1, "team2": team2, "limit": limit},
        )
