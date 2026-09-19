"""History / grading-input tools. Sandbox=30d, Hobby=90d, Builder+=full vault
(get_gamelogs/get_boxscore/get_results); get_lines_history stays Builder+."""

from __future__ import annotations

from typing import Any, Dict

from kashrock_mcp.http import api_get, fail, ok


def _clean_ref(value: str) -> str:
    text = (value or "").strip()
    if not text or text.lower() in {"none", "null", "undefined", "nil"}:
        return ""
    return text


def register_history(mcp: Any) -> None:
    @mcp.tool()
    async def get_gamelogs(sport: str, player: str, limit: int = 200) -> Any:
        """Per-map player gamelogs (kills, ADR, gold, GPM, hero when present) — raw
        performance rows, not settled bet grades (use get_results for those).

        Params:
          sport (str, e.g. "cs2"): required.
          player (str, e.g. "s1mple"): slug, nickname, or kr_pl_*.
          limit (int, e.g. 200): row cap, max 5000.

        Returns: {gamelogs:[...]} one row per map.
        Sandbox=last 30 days, Hobby=last 90 days, Builder+=full vault.
        """
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
    async def get_boxscore(sport: str, match_id: str = "", limit: int = 20) -> Any:
        """One match's full detail, or a recent list. A bare kr_match_id returns a
        lightweight match summary; a plain slug returns the full vault box score +
        STARTER/SUB lineup + sport-native model fields. Not live — use
        get_live_boxscore for in-progress games. For discovery/search across many
        matches use get_matches.

        Params:
          sport (str, e.g. "cs2"): required.
          match_id (str, e.g. "team-a-vs-team-b-20-09-2026"): kr_match_id or slug from
            get_matches (never a provider numeric id). Omit for a recent list.
          limit (int, e.g. 20): match_id omitted only — recent list row cap, max 100.

        Returns: match_id set -> single match/box score object; omitted -> {boxscores:[...]} recent list.
        Sandbox=last 30 days, Hobby=last 90 days, Builder+=full vault.
        """
        mid = _clean_ref(match_id)
        if mid:
            if mid.startswith("kr_"):
                data = await api_get(f"/v6/esports/{sport}/matches/id/{mid}")
            else:
                data = await api_get(f"/v6/esports/{sport}/matches/{mid}/boxscore")
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            return ok(data, sport=sport, filters={"match_id": mid})
        data = await api_get(
            f"/v6/esports/{sport}/boxscores",
            {"limit": max(1, min(int(limit or 20), 100))},
        )
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"match_id": None})

    @mcp.tool()
    async def get_results(sport: str, grade: str = "") -> Any:
        """Settled prop grades: hit | miss | push | pending | error — verdicts, not raw
        performance rows (use get_gamelogs for those).

        Params:
          sport (str, e.g. "cs2"): required.
          grade (str, e.g. "hit"): filter to one grade value.

        Returns: {results:[...]} one row per graded prop.
        Sandbox=last 30 days, Hobby=last 90 days, Builder+=full vault.
        """
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
        sport: str = "",
        match_id: str = "",
        prop_id: str = "",
        book: str = "",
        market: str = "",
        market_key: str = "",
    ) -> Any:
        """Opening/closing team mainlines for a match, or the quote tape for one prop.
        Vault history only — for in-play line movement while a match is live, use
        get_live_odds(history=true).

        Params:
          sport (str, e.g. "cs2"): required when match_id is set.
          match_id (str, e.g. "team-a-vs-team-b-20-09-2026"): slug or kr_match_id —
            returns that match's opening/closing mainlines. Mutually exclusive with prop_id/market_key.
          prop_id (str, e.g. "12345"): with book, returns that prop's quote tape.
          book (str, e.g. "prizepicks"): pairs with prop_id.
          market (str, e.g. "match_winner"): match_id mode only — filter to one market.
          market_key (str, e.g. "cs2:kills_map_1:s1mple"): alternative to prop_id+book
            for the quote tape.

        Returns: match_id set -> {markets:[...]} opening/closing prints;
        prop_id/market_key set -> {tape:[...]} quote history.
        Builder+.
        """
        if match_id:
            slug = _clean_ref(match_id)
            if not slug:
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
                hint="Vault closing prints. In-play steam is get_live_odds(history=true).",
            )

        if market_key or (prop_id and book):
            params = {}
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

        return fail("Provide match_id (with sport), or market_key, or prop_id and book.", status=400)
