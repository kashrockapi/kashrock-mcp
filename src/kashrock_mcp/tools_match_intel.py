"""Match prep intel — team stats, player boards, tournament maps."""

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
        view: str = "team_stats",
        team1: str = "",
        team2: str = "",
        date: str = "",
    ) -> Any:
        """Pre-match intel for one match: team stats and map pool, the player
        weapon/agent board, or CS2 tournament map picks/bans. Needs a KashRock
        match_slug or kr_match_id from get_matches — never a provider numeric id.

        Params:
          sport (str, e.g. "cs2"): view=team_stats supports cs2|r6|cod|valorant|apex;
            view=player_board supports cs2|valorant only; view=tournament_maps is cs2-only.
          match_slug (str, e.g. "team-a-vs-team-b-20-09-2026"): required.
          view (str, e.g. "team_stats"): team_stats (default; team form, mode/map
            winrates, map pool & side biases, key player matchups, betting insights) |
            player_board (player averages + favourite weapons or agent/role board) |
            tournament_maps (CS2 map picks/bans + T/CT winrates).
          team1 / team2 (str, e.g. "Natus Vincere"): team_stats/player_board only —
            optional disambiguation when the slug is ambiguous.
          date (str, e.g. "2026-09-20"): team_stats/player_board only — optional disambiguation.

        Returns: team_stats -> prep board object; player_board -> {teams:[{players:[...]}]};
        tournament_maps -> {maps:[...]}.
        Builder+.
        """
        bad = _bad_ref(match_slug, label="match_slug")
        if bad:
            return bad
        sp = (sport or "").strip().lower()
        v = (view or "team_stats").strip().lower()
        slug = match_slug.strip()

        if v == "tournament_maps":
            if sp != "cs2":
                return fail("view=tournament_maps is CS2-only.", status=400)
            data = await api_get(f"/v6/esports/cs2/matches/{slug}/tournament-maps")
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            maps = list((data or {}).get("maps") or []) if isinstance(data, dict) else []
            return ok(
                data,
                sport="cs2",
                total=len(maps),
                returned=len(maps),
                filters={"match_slug": slug, "view": v},
            )

        if v == "player_board":
            if sp not in {"cs2", "valorant"}:
                return fail("view=player_board supports cs2 and valorant.", status=400)
            params: Dict[str, Any] = {}
            if team1.strip():
                params["team1"] = team1.strip()
            if team2.strip():
                params["team2"] = team2.strip()
            if date.strip():
                params["date"] = date.strip()
            data = await api_get(f"/v6/esports/{sp}/matches/{slug}/player-board", params or None)
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
                    "match_slug": slug,
                    "view": v,
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

        # team_stats (default)
        if sp not in {"cs2", "r6", "cod", "valorant", "apex"}:
            return fail("view=team_stats supports cs2, r6, cod, valorant, and apex.", status=400)
        params = {}
        if team1.strip():
            params["team1"] = team1.strip()
        if team2.strip():
            params["team2"] = team2.strip()
        if date.strip():
            params["date"] = date.strip()
        data = await api_get(f"/v6/esports/{sp}/matches/{slug}/prep", params or None)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(
            data,
            sport=sp,
            filters={
                "match_slug": slug,
                "view": v,
                "team1": team1.strip() or None,
                "team2": team2.strip() or None,
                "date": date.strip() or None,
            },
        )
