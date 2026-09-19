"""Plan → unlocked MCP capabilities (mirrors API middleware gates)."""

from __future__ import annotations

from typing import Any, Dict, List

SPORTS = ["cs2", "valorant", "lol", "dota2", "cod", "r6", "mlbb", "deadlock", "apex"]

MARKETS = {
    "props": [
        "CS2_KILLS_MAP_1",
        "CS2_KILLS_MAP_2",
        "CS2_KILLS_MAPS_1_2",
        "CS2_HEADSHOTS_MAP_1",
        "CS2_MONEYLINE",
        "CS2_MONEYLINE_MAP_1",
        "LOL_KILLS_MAPS_1_3",
        "LOL_MONEYLINE",
    ],
    "lines": ["match_winner", "map_winner", "total_maps", "map_handicap"],
}

# tool_id → (min_plan_rank, one-line when to use). Rank is the LOWEST tier that
# unlocks any mode of the tool; higher-gated modes/views are called out in the
# "when" text itself, since real enforcement happens server-side per endpoint.
_TOOLS: Dict[str, tuple[int, str]] = {
    "login": (0, "Google sign-in; stores API key locally."),
    "get_identity": (0, "Your plan, quota, and (include_capabilities=true) full tool inventory."),
    "get_guidance": (0, "Local helper: mode=catalog (sports/markets free, books needs Hobby+), error, or build."),
    "get_props": (0, "DFS player props (or coverage_only=true for per-book counts). Sandbox=CS2 (500 req/UTC day); Hobby+=all sports."),
    "get_player_props": (0, "DFS + sportsbook named-player props, optional include_media. board=dfs|main|all; default view=groups+slim."),
    "get_lines": (1, "Team mainlines: view=consensus (default, Hobby+) | best_edges (Hobby+) | moneyline (Hobby+)."),
    "get_gaps": (1, "DFS book-vs-book line spreads (same prop, different lines). Hobby+."),
    "get_media": (0, "Resolve player faces + team logos by name/id."),
    "get_player": (0, "q=search (nickname→kr_pl_*) or view=profile|stats (Sandbox=CS2) | stats_full (Hobby+)."),
    "get_rankings": (0, "Player rankings board. Sandbox=CS2."),
    "get_research": (1, "mode=board|board_tapes|player research slips/tapes. Hobby+."),
    "get_matches": (0, "List/search matches (Sandbox=CS2); team=full vault schedule or h2h=true needs Builder+."),
    "get_boxscore": (0, "One match's full detail by kr_match_id/slug, or a recent list. Sandbox=last 30 days, Hobby=last 90 days, Builder+=full vault."),
    "get_streams": (1, "Live Twitch/Kick streams for a sport. Hobby+."),
    "get_match_prep": (2, "view=team_stats|player_board|tournament_maps. CS2, R6, COD, Valorant & Apex per view. Builder+."),
    "get_live_boxscore": (0, "view=boxscore|frame|events, or omit game_id to list live games. Sandbox=CS2 REST 30-60s delayed; Hobby=all sports 5s delayed; Builder+=real-time."),
    "get_live_odds": (1, "In-play odds, or history=true for the shift audit log. Hobby+."),
    "get_results": (0, "Settled prop grades (hit/miss/push). Sandbox=last 30 days, Hobby=last 90 days, Builder+=full vault."),
    "get_gamelogs": (0, "Per-map player history for grading (up to 5000 maps). Sandbox=last 30 days, Hobby=last 90 days, Builder+=full vault."),
    "get_lines_history": (2, "Opening/closing team mainlines (match_id) or a prop quote tape (prop_id+book / market_key). Builder+."),
}

_PLAN_RANK = {
    "sandbox": 0,
    "hobby": 1,
    "builder": 2,
    "pro": 3,
    "master": 3,
}


def plan_rank(plan: str) -> int:
    return _PLAN_RANK.get((plan or "sandbox").lower(), 0)


def capabilities_for(plan: str) -> Dict[str, Any]:
    rank = plan_rank(plan)
    unlocked: List[Dict[str, str]] = []
    locked: List[Dict[str, str]] = []
    for tool, (need, when) in _TOOLS.items():
        row = {"tool": tool, "when": when}
        if rank >= need:
            unlocked.append(row)
        else:
            need_name = next(k for k, v in _PLAN_RANK.items() if v == need and k != "master")
            row["requires"] = need_name
            locked.append(row)
    return {
        "plan": plan,
        "unlocked": unlocked,
        "locked": locked,
        "upgrade_url": "https://www.kashrock.com/pricing",
        "note": "Stacks are not exposed via public API or MCP. Use job tools — do not invent endpoints.",
    }
