"""Live in-game frames / boxscores / events. Sandbox=30-60s delayed (CS2),
Hobby=5s delayed (all sports), Builder+=real-time (<2s SLA). Live odds
(get_live_odds/get_live_odds_history) are Hobby+. The WebSocket wire
(get_live_ws) stays Builder+."""

from __future__ import annotations

from typing import Any

from kashrock_mcp.http import DEFAULT_API, api_get, fail, ok

# Keep aligned with v6/live/latency.py LIVE_SCOREBOARD_CLAIM / LIVE_WS_PUSH_CLAIM.
_LIVE_SCOREBOARD_CLAIM = (
    "Live player kills, deaths, and assists updated in under 2 seconds"
)
_LIVE_WS_PUSH_CLAIM = "Push updates under 2 seconds after Redis write"


def register_live(mcp: Any) -> None:
    @mcp.tool()
    async def get_live_games(sport: str) -> Any:
        """List games with live in-game telemetry (KDA frames). Sandbox=CS2, 30-60s delayed; Hobby=all sports, 5s delayed; Builder+=real-time. Use game_id with get_live_boxscore."""
        data = await api_get(f"/v6/esports/{sport}/live/games")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        games = list((data or {}).get("games") or []) if isinstance(data, dict) else []
        return ok(
            data,
            sport=sport,
            total=(data or {}).get("total") if isinstance(data, dict) else len(games),
            returned=len(games),
            hint="Pass game_id to get_live_boxscore for the live scoreboard.",
        )

    @mcp.tool()
    async def get_live_boxscore(sport: str, game_id: str = "") -> Any:
        """Live in-game board (K/D/A plus sport-native state: CS2 money/bomb, LoL gold/towers, Deadlock gold/CS/level). Omit game_id to list live games. Sandbox=CS2, 30-60s delayed; Hobby=all sports, 5s delayed; Builder+=real-time."""
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
        data = await api_get(f"/v6/esports/{sport}/live/{gid}/boxscore")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"game_id": gid})

    @mcp.tool()
    async def get_live_frame(sport: str, game_id: str) -> Any:
        """Raw live NormalizedFrame + metadata for one game_id. Sandbox=CS2, 30-60s delayed; Hobby=all sports, 5s delayed; Builder+=real-time."""
        gid = (game_id or "").strip()
        if not gid:
            return fail("Provide game_id from get_live_games.", status=400)
        data = await api_get(f"/v6/esports/{sport}/live/{gid}/frames")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"game_id": gid})

    @mcp.tool()
    async def get_live_events(sport: str, game_id: str) -> Any:
        """Sport-native live events (kills, bomb, towers, roshan, round wins) for one game_id. Sandbox=30-60s delayed, Hobby=5s delayed, Builder+=real-time."""
        gid = (game_id or "").strip()
        if not gid:
            return fail("Provide game_id from get_live_games.", status=400)
        data = await api_get(f"/v6/esports/{sport}/live/{gid}/events")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(
            data,
            sport=sport,
            total=(data or {}).get("total") if isinstance(data, dict) else None,
            filters={"game_id": gid},
        )

    @mcp.tool()
    async def get_live_odds(sport: str, game_id: str = "", status: str = "all") -> Any:
        """Shifting betting odds (live in-play and pre-match steam moves) and markets across premier sportsbooks. Hobby+. Omit game_id to list matches with odds. Optional status=all|live|prematch."""
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
        data = await api_get(f"/v6/esports/{sport}/live/{gid}/odds")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"game_id": gid})

    @mcp.tool()
    async def get_live_odds_history(sport: str, game_id: str) -> Any:
        """Audit log of in-game odds shifts and line movements for one match. Hobby+."""
        gid = (game_id or "").strip()
        if not gid:
            return fail("Provide game_id (match slug or kr_match_id).", status=400)
        data = await api_get(f"/v6/esports/{sport}/live/{gid}/odds/history")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport, filters={"game_id": gid})

    @mcp.tool()
    async def get_live_ws(sport: str = "cs2") -> Any:
        """Live push WebSocket contract (Builder+). Returns URL, auth, subscribe ops — connect from your app; MCP cannot hold the socket."""
        sport_key = (sport or "cs2").strip().lower() or "cs2"
        base = DEFAULT_API.replace("https://", "wss://").replace("http://", "ws://")
        path = "/v6/esports/live/ws"
        return ok(
            {
                "url": f"{base}{path}",
                "url_with_key": f"{base}{path}?api_key=YOUR_API_KEY",
                "auth": [
                    "Query: ?api_key=…",
                    "Header: Authorization: Bearer …",
                    "Header: x-api-key: …",
                ],
                "plan": "Builder or Pro (sandbox/hobby rejected at handshake)",
                "latency": {
                    "scoreboard_sla_seconds": 2,
                    "scoreboard_claim": _LIVE_SCOREBOARD_CLAIM,
                    "ws_push_claim": _LIVE_WS_PUSH_CLAIM,
                },
                "rate_limits": "WS connect, subscribe, and push ticks do not count against HTTP req/min",
                "caps": "Builder: 2 connections / 5 match subs. Pro: 10 connections / 25 match subs + game_id=*. Enforced when ENABLE_WS_CAPS is on.",
                "hello": {
                    "op": "hello",
                    "plan": "<your_plan>",
                    "ws_limits": {"max_connections": "…", "max_subscriptions": "…"},
                    "latency": {"scoreboard_sla_seconds": 2},
                },
                "subscribe": {
                    "op": "subscribe",
                    "sport": sport_key,
                    "game_id": "<game_id from get_live_games>|*",
                },
                "unsubscribe": {"op": "unsubscribe", "sport": sport_key, "game_id": "<id>|*"},
                "ping": {"op": "ping"},
                "pushes": {
                    "snapshot": "Full boxscore + meta + odds for one game_id",
                    "games_list": "Live games list when subscribed to game_id=*",
                    "frame": "NormalizedFrame tick",
                    "boxscore": "Derived K/D/A scoreboard tick",
                    "meta": "Round / map / clock",
                    "event": "Derived kill/death events batch",
                    "odds": "Live odds tick when present",
                    "pong": "Reply to ping",
                },
                "http_equivalents": {
                    "games": f"GET /v6/esports/{sport_key}/live/games",
                    "boxscore": f"GET /v6/esports/{sport_key}/live/{{game_id}}/boxscore",
                    "frames": f"GET /v6/esports/{sport_key}/live/{{game_id}}/frames",
                    "events": f"GET /v6/esports/{sport_key}/live/{{game_id}}/events",
                },
                "http_path": path,
            },
            sport=sport_key,
            hint=(
                f"{_LIVE_WS_PUSH_CLAIM}. Connect with your API key, then subscribe. "
                "List game_ids via get_live_games; use game_id='*' for all games in a sport."
            ),
        )

