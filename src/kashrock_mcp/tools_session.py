"""Session tools: identity/capabilities and a local helper (catalog/error/build)."""

from __future__ import annotations

from typing import Any

from kashrock_mcp.catalog import MARKETS, SPORTS, capabilities_for
from kashrock_mcp.creds import describe, load_credentials, load_key
from kashrock_mcp.http import api_get, fail, ok
from kashrock_mcp.version import version_payload


def register_session(mcp: Any) -> None:
    @mcp.tool()
    async def get_identity(include_capabilities: bool = False) -> Any:
        """Your KashRock plan, quota remaining, and (optionally) the full tool inventory.

        Call this first to check who you are and what your plan allows. For a
        goal-driven shortlist of tools instead of the full inventory, use
        get_guidance(mode="build"). For canonical enum values (sports/books/markets),
        use get_guidance(mode="catalog") — not this tool.

        Params:
          include_capabilities (bool, e.g. true): when true, also returns the full
            unlocked/locked tool list for your plan (works even when not signed in,
            showing sandbox capabilities).

        Returns: {plan, source/email, auth, mcp_version, capabilities?} — one identity object.
        """
        ver = await version_payload()
        if not load_key():
            if not include_capabilities:
                return fail("Not signed in. Call login first.", status=401)
            caps = capabilities_for("sandbox")
            return ok(
                {"plan": "sandbox", "signed_in": False, **caps, **ver},
                plan="sandbox",
                hint=ver.get("mcp_update")
                or "Not signed in — showing sandbox capabilities. Call login for your real plan.",
            )
        data = await api_get("/v6/me")
        if isinstance(data, dict) and data.get("ok") is False:
            creds = load_credentials()
            if creds.get("from_env"):
                plan = "master"
                payload: dict = {"plan": plan, "source": "env_key", "auth": describe(), **ver}
                if include_capabilities:
                    payload["capabilities"] = capabilities_for(plan)
                return ok(
                    payload,
                    plan=plan,
                    hint=ver.get("mcp_update")
                    or "API /v6/me not on this host yet — assuming full access for env key.",
                )
            if creds.get("plan") or creds.get("email"):
                plan = str(creds.get("plan") or "sandbox")
                payload = {
                    "email": creds.get("email"),
                    "plan": plan,
                    "source": "local_credentials",
                    "auth": describe(),
                    **ver,
                }
                if include_capabilities:
                    payload["capabilities"] = capabilities_for(plan)
                return ok(
                    payload,
                    plan=plan,
                    hint=ver.get("mcp_update") or "API /v6/me unavailable — showing local credentials.",
                )
            return data
        payload = data if isinstance(data, dict) else {"data": data}
        plan = (data or {}).get("plan") if isinstance(data, dict) else None
        if isinstance(payload, dict):
            payload = {**payload, **ver}
            if include_capabilities:
                payload["capabilities"] = capabilities_for(str(plan or "sandbox"))
        return ok(payload, plan=plan, hint=ver.get("mcp_update"))

    @mcp.tool()
    async def get_guidance(
        mode: str,
        kind: str = "",
        message: str = "",
        goal: str = "",
    ) -> Any:
        """Local helper: canonical reference values, plain-English error fixes, or a
        goal-based tool shortlist. Not live esports data. Use get_identity for your own
        plan/quota, not this tool.

        Params:
          mode (str, e.g. "catalog"): required — catalog | error | build.
          kind (str, e.g. "sports"): mode=catalog only — sports | books | markets.
          message (str, e.g. "403 Hobby plan required"): mode=error only — the raw
            error text to diagnose.
          goal (str, e.g. "DFS prop betting app"): mode=build only — a one-line
            description of what you're building.

        Returns:
          catalog -> {sports:[...]} or {books:{...}} or {markets:{props:[...], lines:[...]}}
          error   -> {fix, tool?, upgrade_url?}
          build   -> {recommended_plan, tools:[...], steps:[...], upgrade_url, mcp_setup}
        """
        m = (mode or "").strip().lower()

        if m == "catalog":
            k = (kind or "").strip().lower()
            if k == "sports":
                return ok({"sports": SPORTS})
            if k == "books":
                data = await api_get("/v6/books")
                if isinstance(data, dict) and data.get("ok") is False:
                    return data
                return ok(data)
            if k == "markets":
                return ok(MARKETS)
            return fail("kind must be sports, books, or markets.", status=400)

        if m == "error":
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
                        "fix": "Consensus lines need Hobby+. Upgrade, then call get_lines.",
                        "upgrade_url": "https://www.kashrock.com/pricing",
                    }
                )
            if "builder" in text or "historical" in text or "gamelog" in text or "schedule" in text:
                return ok(
                    {
                        "fix": "History/schedule need Builder+. Use get_matches, get_gamelogs, get_lines_history after upgrade.",
                        "upgrade_url": "https://www.kashrock.com/pricing",
                    }
                )
            if "sandbox" in text and "cs2" in text:
                return ok(
                    {
                        "fix": "Sandbox is CS2 only (props, matches, players, live REST). Upgrade to Hobby for other sports and lines.",
                        "upgrade_url": "https://www.kashrock.com/pricing",
                    }
                )
            return ok(
                {"fix": "Check get_identity(include_capabilities=true), then retry with plan-unlocked tools."}
            )

        if m == "build":
            text = (goal or "").lower()
            tools: list[str] = ["get_identity"]
            plan = "hobby"
            steps: list[str] = []

            if any(w in text for w in ("prop", "prizepicks", "underdog", "dfs", "kills", "headshot")):
                tools += ["get_props", "get_player_props", "get_media"]
                steps.append("DFS: get_props. DFS+sportsbook: get_player_props. Media: get_player_props(include_media=true) or get_media.")
            if any(w in text for w in ("logo", "image", "face", "avatar", "media", "headshot")):
                tools += ["get_media", "get_player_props"]
                steps.append("Prop cards already have links.player_image; resolve by name with get_media.")
            if any(w in text for w in ("moneyline", "odds", "kalshi", "polymarket", "consensus", "fair", "best line")):
                tools += ["get_lines"]
                steps.append("Consensus with get_lines(view=consensus); top edges with view=best_edges; flattened team odds with view=moneyline.")
            if any(w in text for w in ("gap", "line shop", "book vs book")):
                tools += ["get_gaps"]
                steps.append("DFS line shopping: get_gaps (not model edges).")
            if any(
                w in text
                for w in ("grade", "gamelog", "history", "settle", "backtest", "tape", "closing", "close")
            ):
                tools += ["get_gamelogs", "get_results", "get_lines_history", "get_boxscore"]
                plan = "builder"
                steps.append(
                    "Builder: bind propId at placement, grade with get_gamelogs + get_lines_history(prop_id/market_key). Closing mainlines: get_lines_history(match_id)."
                )
            if any(
                w in text
                for w in ("prep", "map pool", "favourite weapon", "favorite weapon", "fav weapon", "player board", "tournament map")
            ):
                tools += ["get_match_prep", "get_matches"]
                plan = "builder"
                steps.append("CS2/Valorant intel: get_match_prep(view=team_stats|player_board|tournament_maps).")
            if any(w in text for w in ("schedule", "fixture", "upcoming", "live match", "matchup", "team schedule")):
                tools += ["get_matches"]
                plan = "builder"
                steps.append("Builder: get_matches(team=...) for a team's full vault schedule; get_matches(team1, team2) to search.")
            if any(
                w in text
                for w in (
                    "live stats", "in-game", "ingame", "scoreboard", "live kda", "k/d/a",
                    "live frame", "live boxscore", "websocket", "web socket", "live ws", "push feed",
                )
            ):
                tools += ["get_live_boxscore"]
                plan = "builder"
                steps.append("Live KDA: get_live_boxscore(sport) → game_id → get_live_boxscore(sport, game_id, view=boxscore|frame|events).")
            if any(w in text for w in ("player", "kpr", "ranking", "research", "h2h", "stream")):
                tools += ["get_player", "get_rankings", "get_research", "get_matches", "get_streams"]
                steps.append("Resolve identity with get_player(q=...); deepen with view=stats_full / get_research / get_matches(team1,team2,h2h=true).")
            if not steps:
                tools += ["get_props", "get_lines"]
                steps.append("Start with get_props + get_lines; call get_guidance(mode=catalog, kind=markets) for names.")

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
                hint="Call login once, then get_identity, then the tools listed — never invent HTTP paths.",
            )

        return fail("mode must be catalog, error, or build.", status=400)
