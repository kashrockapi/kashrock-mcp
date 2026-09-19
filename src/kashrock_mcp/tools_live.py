"""Live in-game state and in-play odds. Sandbox=30-60s delayed (CS2),
Hobby=5s delayed (all sports), Builder+=real-time (<2s SLA). Live odds are Hobby+.
The WebSocket wire is direct-plan/API only and is not exposed through MCP."""

from __future__ import annotations

from typing import Any

from kashrock_mcp.http import api_get, ok


def register_live(mcp: Any) -> None:
    @mcp.tool()
    async def get_live_boxscore(sport: str, game_id: str = "", view: str = "boxscore") -> Any:
        """Live in-game state: K/D/A boxscore, the raw normalized frame, or discrete
        events (kills, bomb, towers, roshan, round wins). Omit game_id to list live
        games regardless of view. Not odds — use get_live_odds. Not vault history —
        use get_boxscore/get_gamelogs.

        Params:
          sport (str, e.g. "cs2"): required.
          game_id (str, e.g. "1234567"): from the games list; omit this to get that list.
          view (str, e.g. "boxscore"): boxscore (default; K/D/A plus sport-native state:
            CS2 money/bomb, LoL gold/towers, Deadlock gold/CS/level) | frame (raw
            NormalizedFrame + metadata) | events (discrete event log). Ignored when game_id is omitted.

        Returns: game_id omitted -> {games:[...]}; boxscore -> scoreboard object;
        frame -> NormalizedFrame; events -> {events:[...]}.
        Sandbox=CS2, 30-60s delayed; Hobby=all sports, 5s delayed; Builder+=real-time.
        """
        gid = (game_id or "").strip()
        if not gid:
            data = await api_get(f"/v6/esports/{sport}/live/games")
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            games = list((data or {}).get("games") or []) if isinstance(data, dict) else []
            return ok(
                data,
                sport=sport,
                total=(data or {}).get("total") if isinstance(data, dict) else len(games),
                returned=len(games),
                hint="Pick a game_id from games[], then call get_live_boxscore again.",
            )

        v = (view or "boxscore").strip().lower()

        if v == "frame":
            data = await api_get(f"/v6/esports/{sport}/live/{gid}/frames")
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            return ok(data, sport=sport, filters={"game_id": gid, "view": v})

        if v == "events":
            data = await api_get(f"/v6/esports/{sport}/live/{gid}/events")
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            return ok(
                data,
                sport=sport,
                total=(data or {}).get("total") if isinstance(data, dict) else None,
                filters={"game_id": gid, "view": v},
            )

        # boxscore (default)
        data = await api_get(f"/v6/esports/{sport}/live/{gid}/boxscore")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"game_id": gid, "view": "boxscore"})

    @mcp.tool()
    async def get_live_odds(
        sport: str, game_id: str = "", status: str = "all", history: bool = False
    ) -> Any:
        """Shifting in-play betting odds and active markets, or the audit log of past
        shifts for one match. Not in-game score/state — use get_live_boxscore.

        Params:
          sport (str, e.g. "cs2"): required.
          game_id (str, e.g. "team-a-vs-team-b-20-09-2026"): match slug or kr_match_id.
            Omit to list matches with odds.
          status (str, e.g. "all"): all | live | prematch. Only used when game_id is omitted.
          history (bool, e.g. false): true returns the in-play shift/line-movement
            audit log for game_id instead of current odds.

        Returns: game_id omitted -> {games:[...]}; history=false -> current odds/markets;
        history=true -> {shifts:[...]} audit log.
        Hobby+.
        """
        gid = (game_id or "").strip()
        if not gid:
            stat = (status or "all").strip().lower()
            data = await api_get(f"/v6/esports/{sport}/live/odds?status={stat}")
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            games = list((data or {}).get("games") or []) if isinstance(data, dict) else []
            return ok(
                data,
                sport=sport,
                total=(data or {}).get("total") if isinstance(data, dict) else len(games),
                returned=len(games),
                hint="Pass match_slug or kr_match_id to get_live_odds for market prices & shifts.",
            )
        if history:
            data = await api_get(f"/v6/esports/{sport}/live/{gid}/odds/history")
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            return ok(data, sport=sport, filters={"game_id": gid, "history": True})
        data = await api_get(f"/v6/esports/{sport}/live/{gid}/odds")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"game_id": gid, "history": False})
