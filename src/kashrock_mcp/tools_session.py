"""Session tools: whoami, capabilities, sports, books, markets."""

from __future__ import annotations

from typing import Any

from kashrock_mcp.catalog import MARKETS, SPORTS, capabilities_for
from kashrock_mcp.creds import describe, load_credentials, load_key
from kashrock_mcp.http import api_get, fail, ok
from kashrock_mcp.version import version_payload


def register_session(mcp: Any) -> None:
    @mcp.tool()
    async def whoami() -> Any:
        """Your KashRock plan, quota remaining, and unlocked data drawers."""
        if not load_key():
            return fail("Not signed in. Call login first.", status=401)
        ver = await version_payload()
        data = await api_get("/v6/me")
        if isinstance(data, dict) and data.get("ok") is False:
            creds = load_credentials()
            if creds.get("from_env"):
                plan = "master"
                return ok(
                    {
                        "plan": plan,
                        "source": "env_key",
                        "auth": describe(),
                        "unlocked": [t["tool"] for t in capabilities_for(plan)["unlocked"]],
                        **ver,
                    },
                    plan=plan,
                    hint=ver.get("mcp_update")
                    or "API /v6/me not on this host yet — assuming full access for env key.",
                )
            if creds.get("plan") or creds.get("email"):
                plan = str(creds.get("plan") or "sandbox")
                return ok(
                    {
                        "email": creds.get("email"),
                        "plan": plan,
                        "source": "local_credentials",
                        "auth": describe(),
                        "unlocked": [t["tool"] for t in capabilities_for(plan)["unlocked"]],
                        **ver,
                    },
                    plan=plan,
                    hint=ver.get("mcp_update")
                    or "API /v6/me unavailable — showing local credentials.",
                )
            return data
        payload = data if isinstance(data, dict) else {"data": data}
        if isinstance(payload, dict):
            payload = {**payload, **ver}
        return ok(
            payload,
            plan=(data or {}).get("plan") if isinstance(data, dict) else None,
            hint=ver.get("mcp_update"),
        )

    @mcp.tool()
    async def list_capabilities() -> Any:
        """Tools available for your current plan — call whoami first if unsure of plan."""
        plan = "sandbox"
        if load_key():
            me = await api_get("/v6/me")
            if isinstance(me, dict) and me.get("ok") is not False:
                plan = str(me.get("plan") or "sandbox")
            elif load_credentials().get("from_env"):
                plan = "master"
            else:
                plan = str(load_credentials().get("plan") or "sandbox")
        ver = await version_payload()
        caps = capabilities_for(plan)
        return ok({**caps, **ver}, plan=plan, hint=ver.get("mcp_update"))

    @mcp.tool()
    async def list_sports() -> Any:
        """Sports KashRock covers."""
        return ok({"sports": SPORTS})

    @mcp.tool()
    async def list_books() -> Any:
        """Live book registry (DFS apps + sportsbooks including Pinnacle, Bovada, Thunderpick, Cloudbet, BetRivers + Kalshi/Polymarket)."""
        data = await api_get("/v6/books")
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data)

    @mcp.tool()
    async def list_markets() -> Any:
        """Canonical prop stat_types and /lines market names agents should use."""
        return ok(MARKETS)

    @mcp.tool()
    async def explain_error(message: str) -> Any:
        """Turn an API/MCP error string into a plain-English next step."""
        text = (message or "").lower()
        if "api key" in text or "not signed" in text or "401" in text:
            return ok(
                {
                    "fix": "Call login (Google in browser) or set KASHROCK_API_KEY.",
                    "tool": "login",
                }
            )
        if "hobby" in text and ("lines" in text or "consensus" in text):
            return ok(
                {
                    "fix": "Consensus lines need Hobby+. Upgrade, then call get_lines or get_moneylines.",
                    "upgrade_url": "https://www.kashrock.com/pricing",
                }
            )
        if "builder" in text or "historical" in text or "gamelog" in text or "schedule" in text:
            return ok(
                {
                    "fix": "History/schedule need Builder+. Use get_matches, get_gamelogs, get_history_tape after upgrade.",
                    "upgrade_url": "https://www.kashrock.com/pricing",
                }
            )
        if "sandbox" in text and "cs2" in text:
            return ok(
                {
                    "fix": "Sandbox is CS2 only (props, matches, players, live REST). Upgrade to Hobby for other sports and moneylines.",
                    "upgrade_url": "https://www.kashrock.com/pricing",
                }
            )
        return ok(
            {"fix": "Check whoami + list_capabilities, then retry with plan-unlocked tools."}
        )

    @mcp.tool()
    async def suggest_build(goal: str) -> Any:
        """Given a one-line app goal, return which MCP tools + plan to use (no endpoints required)."""
        text = (goal or "").lower()
        tools: list[str] = ["whoami", "list_capabilities"]
        plan = "hobby"
        steps: list[str] = []

        if any(w in text for w in ("prop", "prizepicks", "underdog", "dfs", "kills", "headshot")):
            tools += ["get_props", "get_player_props", "get_player_snapshot", "get_coverage", "list_books"]
            steps.append("DFS: get_props. DFS+sportsbook: get_player_props. One player: get_player_snapshot.")
        if any(w in text for w in ("logo", "image", "face", "avatar", "media", "headshot")):
            tools += ["get_media", "get_player_snapshot", "get_props"]
            steps.append("Prop cards already have links.player_image; resolve by name with get_media.")
        if any(w in text for w in ("moneyline", "odds", "kalshi", "polymarket", "consensus", "fair", "best line")):
            tools += ["get_lines", "get_best_lines", "get_moneylines", "get_coverage"]
            steps.append("Pull consensus with get_lines; top edges with get_best_lines.")
        if any(w in text for w in ("gap", "line shop", "book vs book")):
            tools += ["get_gaps"]
            steps.append("DFS line shopping: get_gaps (not model edges).")
        if any(
            w in text
            for w in (
                "grade",
                "gamelog",
                "history",
                "settle",
                "backtest",
                "tape",
                "closing",
                "close",
            )
        ):
            tools += [
                "get_gamelogs",
                "get_results",
                "get_history_tape",
                "get_lines_history",
                "get_boxscore",
            ]
            plan = "builder"
            steps.append(
                "Builder: bind propId at placement, grade with gamelogs + history tape. Closing mainlines: get_lines_history."
            )
        if any(
            w in text
            for w in (
                "prep",
                "map pool",
                "favourite weapon",
                "favorite weapon",
                "fav weapon",
                "player board",
                "tournament map",
            )
        ):
            tools += ["get_match_prep", "get_player_board", "get_tournament_maps", "search_matches"]
            plan = "builder"
            steps.append(
                "CS2/Valorant intel: get_match_prep / get_player_board / get_tournament_maps (CS2)."
            )
        if any(w in text for w in ("schedule", "fixture", "upcoming", "live match", "matchup", "team schedule")):
            tools += ["get_matches", "search_matches", "get_match", "get_team_matches"]
            plan = "builder"
            steps.append("Builder: get_matches / get_team_matches for schedule + vault history.")
        if any(
            w in text
            for w in (
                "live stats",
                "in-game",
                "ingame",
                "scoreboard",
                "live kda",
                "k/d/a",
                "live frame",
                "live boxscore",
                "websocket",
                "web socket",
                "live ws",
                "push feed",
            )
        ):
            tools += [
                "get_live_games",
                "get_live_boxscore",
                "get_live_frame",
                "get_live_events",
                "get_live_ws",
            ]
            plan = "builder"
            steps.append(
                "Live KDA: get_live_boxscore(sport) → game_id. For push: get_live_ws then connect WS from your app."
            )
        if any(w in text for w in ("player", "kpr", "ranking", "research", "h2h", "stream")):
            tools += [
                "search_players",
                "get_player_stats_full",
                "get_rankings",
                "research_player",
                "get_team_h2h",
                "get_streams",
            ]
            steps.append("Resolve identity with search_players; deepen with stats_full / research / h2h.")
        if not steps:
            tools += ["get_props", "get_lines", "list_markets"]
            steps.append("Start with get_props + get_lines; call list_markets for names.")

        ordered: list[str] = []
        for t in tools:
            if t not in ordered:
                ordered.append(t)
        return ok(
            {
                "goal": goal,
                "recommended_plan": plan,
                "tools": ordered,
                "steps": steps,
                "upgrade_url": "https://www.kashrock.com/pricing",
                "mcp_setup": "https://www.kashrock.com/mcp",
            },
            plan=plan,
            hint="Call login once, then whoami, then the tools listed — never invent HTTP paths.",
        )
