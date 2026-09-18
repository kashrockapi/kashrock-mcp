"""CS2 match intel tools — prep board, player weapons, tournament maps."""

from __future__ import annotations

from typing import Any, Dict

from kashrock_mcp.http import api_get, fail, ok


def _bad_ref(value: str, *, label: str) -> Any:
    text = (value or "").strip()
    if not text or text.lower() in {"none", "null", "undefined", "nil"}:
        return fail(
            f"Invalid {label} — use slug or kr_match_id from get_matches "
            "(team-a-vs-team-b-DD-MM-YYYY), never a provider numeric id.",
            status=400,
        )
    if text.isdigit():
        return fail(
            f"Invalid {label} — numeric provider ids are not accepted. "
            "Use match_slug or kr_match_id from get_matches.",
            status=400,
        )
    return None


def register_match_intel(mcp: Any) -> None:
    @mcp.tool()
    async def get_match_prep(
        sport: str,
        match_slug: str,
        team1: str = "",
        team2: str = "",
        date: str = "",
    ) -> Any:
        """Match prep board: team stats, mode winrates, map pool & side biases, form, key player matchups, betting insights. sport = cs2, r6, cod, valorant, or apex. match_slug = KashRock -vs- slug or kr_match_id. Builder+."""
        bad = _bad_ref(match_slug, label="match_slug")
        if bad:
            return bad
        sp = (sport or "").strip().lower()
        if sp not in {"cs2", "r6", "cod", "valorant", "apex"}:
            return fail("get_match_prep supports cs2, r6, cod, valorant, and apex.", status=400)
        params: Dict[str, Any] = {}
        if team1.strip():
            params["team1"] = team1.strip()
        if team2.strip():
            params["team2"] = team2.strip()
        if date.strip():
            params["date"] = date.strip()
        data = await api_get(
            f"/v6/esports/{sp}/matches/{match_slug.strip()}/prep",
            params or None,
        )
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(
            data,
            sport=sp,
            filters={
                "match_slug": match_slug.strip(),
                "team1": team1.strip() or None,
                "team2": team2.strip() or None,
                "date": date.strip() or None,
            },
        )

    @mcp.tool()
    async def get_player_board(
        sport: str,
        match_slug: str,
        team1: str = "",
        team2: str = "",
        date: str = "",
    ) -> Any:
        """Player averages + favourite weapons (CS2) or agent/role board (Valorant). match_slug = KashRock -vs- slug or kr_match_id (not provider ids). Builder+."""
        bad = _bad_ref(match_slug, label="match_slug")
        if bad:
            return bad
        sp = (sport or "").strip().lower()
        if sp not in {"cs2", "valorant"}:
            return fail("get_player_board supports cs2 and valorant.", status=400)
        params: Dict[str, Any] = {}
        if team1.strip():
            params["team1"] = team1.strip()
        if team2.strip():
            params["team2"] = team2.strip()
        if date.strip():
            params["date"] = date.strip()
        data = await api_get(
            f"/v6/esports/{sp}/matches/{match_slug.strip()}/player-board",
            params or None,
        )
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        teams = list((data or {}).get("teams") or []) if isinstance(data, dict) else []
        players = sum(len(t.get("players") or []) for t in teams if isinstance(t, dict))
        return ok(
            data,
            sport=sp,
            total=players,
            returned=players,
            filters={
                "match_slug": match_slug.strip(),
                "team1": team1.strip() or None,
                "team2": team2.strip() or None,
                "date": date.strip() or None,
            },
            hint=(
                "favourite_weapons is top-3 by kills; timeframe is THREE_MONTHS."
                if sp == "cs2"
                else "agents/roles from competitive VCT/VCL; timeframe is 90d_competitive."
            ),
        )

    @mcp.tool()
    async def get_tournament_maps(sport: str, match_slug: str) -> Any:
        """CS2 tournament map picks/bans + T/CT winrates for a match. match_slug = KashRock -vs- slug or kr_match_id. Builder+."""
        bad = _bad_ref(match_slug, label="match_slug")
        if bad:
            return bad
        if (sport or "").strip().lower() != "cs2":
            return fail("get_tournament_maps is CS2-only.", status=400)
        data = await api_get(
            f"/v6/esports/cs2/matches/{match_slug.strip()}/tournament-maps"
        )
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        maps = list((data or {}).get("maps") or []) if isinstance(data, dict) else []
        return ok(
            data,
            sport="cs2",
            total=len(maps),
            returned=len(maps),
            filters={"match_slug": match_slug.strip()},
        )
