"""Match discovery (list/search/schedule/h2h) and live streams."""

from __future__ import annotations

from typing import Any, Dict

from kashrock_mcp.http import api_get, ok


def register_schedule(mcp: Any) -> None:
    @mcp.tool()
    async def get_matches(
        sport: str,
        status: str = "upcoming",
        team: str = "",
        team1: str = "",
        team2: str = "",
        h2h: bool = False,
        date: str = "",
        start_date: str = "",
        end_date: str = "",
        limit: int = 200,
        offset: int = 0,
    ) -> Any:
        """Find matches: list by status, search by team name(s), or pull one team's
        full vault schedule or head-to-head history. Returns lightweight match objects
        (kr_match_id, kr_tm_* team ids) — for a full box score with lineup use
        get_boxscore; for live in-game state use get_live_boxscore.

        Params:
          sport (str, e.g. "cs2"): required.
          status (str, e.g. "upcoming"): upcoming | live | finished. Ignored when
            team or team1 is set.
          team (str, e.g. "Natus Vincere"): one team's full finished schedule from the
            vault. Ignores status/team1/team2/date/h2h.
          team1 (str, e.g. "Natus Vincere"): with team2, search for matches between two
            teams. Takes priority over team/status.
          team2 (str, e.g. "FaZe Clan"): pairs with team1.
          h2h (bool, e.g. false): with team1+team2, return finished head-to-head
            meetings from the vault instead of an upcoming/live search.
          date (str, e.g. "2026-09-20"): team1+team2 search only (h2h=false) — YYYY-MM-DD.
          start_date / end_date (str, e.g. "2026-09-01"): status-list mode date range.
          limit (int, e.g. 200): row cap, max 5000.
          offset (int, e.g. 0): pagination offset.

        Returns: {matches:[...]} for list/search/schedule modes, or {meetings, recent:[...]} for h2h mode.
        Sandbox=CS2 for list/search; team schedule and h2h need Builder+.
        """
        if team1:
            if h2h:
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

        if team:
            params = {
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

        # default: list mode
        params = {
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
    async def get_streams(sport: str) -> Any:
        """Live Twitch/Kick streams for a sport (viewer counts + URLs). Not match data —
        use get_matches to find matches.

        Params:
          sport (str, e.g. "cs2"): required.

        Returns: {streams:[...]} with viewer_count and url per row.
        Hobby+.
        """
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
