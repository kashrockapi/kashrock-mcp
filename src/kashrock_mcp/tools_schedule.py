"""Schedule / matches tools (Builder+)."""

from __future__ import annotations

from typing import Any, Dict

from kashrock_mcp.http import api_get, fail, ok


def _clean_ref(value: str) -> str:
    text = (value or "").strip()
    if not text or text.lower() in {"none", "null", "undefined", "nil"}:
        return ""
    return text


def register_schedule(mcp: Any) -> None:
    @mcp.tool()
    async def get_matches(
        sport: str,
        status: str = "upcoming",
        start_date: str = "",
        end_date: str = "",
        limit: int = 200,
        offset: int = 0,
    ) -> Any:
        """Match list (kr_match_id, kr_tm_* team ids). status: upcoming | live | finished. Builder+. finished uses vault history."""
        params: Dict[str, Any] = {
            "status": status or "upcoming",
            "limit": max(1, min(int(limit or 200), 5000)),
            "offset": max(0, int(offset or 0)),
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        data = await api_get(f"/v6/esports/{sport}/matches", params)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        matches = list((data or {}).get("matches") or []) if isinstance(data, dict) else []
        return ok(
            data,
            sport=sport,
            total=len(matches),
            returned=len(matches),
            filters={"status": status, "start_date": start_date, "end_date": end_date},
        )

    @mcp.tool()
    async def get_match(sport: str, match_id: str = "", slug: str = "") -> Any:
        """One match by kr_match_id (preferred) or slug. Teams/players are KashRock ids. Builder+."""
        mid = _clean_ref(match_id) or _clean_ref(slug)
        if not mid:
            return fail(
                "Provide a real match_id (kr_…) or slug from match lists — not None/null.",
                status=400,
            )
        if mid.startswith("kr_"):
            data = await api_get(f"/v6/esports/{sport}/matches/id/{mid}")
        else:
            data = await api_get(f"/v6/esports/{sport}/matches/{mid}/boxscore")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"id": mid})

    @mcp.tool()
    async def search_matches(
        sport: str,
        team1: str,
        team2: str = "",
        date: str = "",
    ) -> Any:
        """Find matches by team name(s) and optional YYYY-MM-DD. Builder+."""
        params: Dict[str, Any] = {"team1": team1}
        if team2:
            params["team2"] = team2
        if date:
            params["date"] = date
        data = await api_get(f"/v6/esports/{sport}/matches/search", params)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        matches = list((data or {}).get("matches") or []) if isinstance(data, dict) else []
        return ok(
            data,
            sport=sport,
            total=len(matches),
            returned=len(matches),
            filters={"team1": team1, "team2": team2, "date": date},
            hint="Use slug from results with get_boxscore.",
        )

    @mcp.tool()
    async def get_team_matches(
        sport: str,
        team: str,
        start_date: str = "",
        end_date: str = "",
        limit: int = 200,
        offset: int = 0,
    ) -> Any:
        """Full finished team schedule from the history vault. Builder+."""
        params: Dict[str, Any] = {
            "limit": max(1, min(int(limit or 200), 5000)),
            "offset": max(0, int(offset or 0)),
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        data = await api_get(f"/v6/esports/{sport}/teams/{team}/matches", params)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        matches = list((data or {}).get("matches") or []) if isinstance(data, dict) else []
        return ok(
            data,
            sport=sport,
            total=(data or {}).get("total") if isinstance(data, dict) else len(matches),
            returned=len(matches),
            filters={
                "team": team,
                "start_date": start_date,
                "end_date": end_date,
                "limit": params["limit"],
                "offset": params["offset"],
            },
            hint="Paginate with offset. Pair with get_boxscore using slug.",
        )

    @mcp.tool()
    async def get_streams(sport: str) -> Any:
        """Live Twitch/Kick streams for a sport (viewer counts + URLs)."""
        data = await api_get(f"/v6/esports/{sport}/streams")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        streams = list((data or {}).get("streams") or []) if isinstance(data, dict) else []
        return ok(
            data,
            sport=sport,
            total=(data or {}).get("total_streams") if isinstance(data, dict) else len(streams),
            returned=len(streams),
        )
