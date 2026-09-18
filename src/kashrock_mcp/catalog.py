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

# tool_id → (min_plan_rank, one-line when to use)
_TOOLS: Dict[str, tuple[int, str]] = {
    "login": (0, "Google sign-in; stores API key locally."),
    "whoami": (0, "Your plan, quota, and unlocked drawers."),
    "list_capabilities": (0, "Which tools this plan can use."),
    "suggest_build": (0, "Map a one-line app goal to tools + plan."),
    "list_sports": (0, "Sports KashRock covers."),
    "list_books": (1, "Live book registry (DFS + sportsbooks including Bovada, Thunderpick, Cloudbet, BetRivers, Pinnacle + Kalshi/Polymarket)."),
    "list_markets": (0, "Canonical market / moneyline names."),
    "get_props": (0, "DFS player props only. Sandbox=CS2 (500 req/UTC day); Hobby+=all sports. Prefer filters + slim."),
    "get_player_props": (
        0,
        "DFS + sportsbook named-player props. board=dfs|main|all; default view=groups+slim.",
    ),
    "get_moneylines": (1, "Team match/map moneylines (line is null — that is normal)."),
    "get_lines": (1, "Consensus team mainlines across sportsbooks, DFS Teams (PrizePicks/Underdog/Sleeper), and prediction markets (upcoming only by default; live_only=false for started)."),
    "get_best_lines": (1, "Top cross-venue consensus edges from /lines (upcoming only by default)."),
    "get_gaps": (1, "DFS book-vs-book line spreads (same prop, different lines)."),
    "get_coverage": (0, "Per-book prop counts / freshness (no prop rows)."),
    "get_media": (0, "Resolve player faces + team logos by name/id."),
    "get_player_snapshot": (0, "Media + slim player-prop groups for one player."),
    "search_players": (0, "Find players by nickname; rows emit kr_pl_*. Sandbox=CS2."),
    "get_player": (0, "Player profile by kr_pl_* or nickname. Sandbox=CS2."),
    "get_player_stats": (0, "Canonical player stats (KPR, etc.). Sandbox=CS2."),
    "get_player_stats_full": (1, "Full aggregate: period + foundation + recent maps."),
    "get_rankings": (0, "Player rankings board. Sandbox=CS2."),
    "research_board": (1, "Research slips for the current board."),
    "research_board_tapes": (1, "Research quote tapes for the live board."),
    "research_player": (1, "Career tape for one player + market. player=kr_pl_* / slug / nick. Empty tape is 200."),
    "get_streams": (1, "Live Twitch/Kick streams for a sport."),
    "get_matches": (0, "Upcoming / live / finished lists with kr_match_id + kr_tm_* team ids. Sandbox=CS2; Builder+ finished vault."),
    "get_match": (0, "One match by kr_match_id or slug. Teams/players are KashRock ids. Sandbox=CS2."),
    "search_matches": (0, "Find a match by team names + date. Sandbox=CS2."),
    "get_team_matches": (2, "Full finished team schedule from the vault."),
    "get_live_games": (0, "Games with live in-game telemetry (list game_ids). Sandbox=CS2 REST, 30-60s delayed; Hobby=all sports, 5s delayed; Builder+=real-time."),
    "get_live_boxscore": (0, "Live in-game board (KDA plus sport state: CS2 money/bomb, LoL gold/towers, Deadlock gold/CS/level). Omit game_id to list games. Sandbox=CS2, 30-60s delayed; Hobby=all sports, 5s delayed; Builder+=real-time."),
    "get_live_frame": (0, "Raw live NormalizedFrame + metadata for one game_id. Sandbox=CS2, 30-60s delayed; Hobby=all sports, 5s delayed; Builder+=real-time."),
    "get_live_events": (0, "Sport-native live events (CS2 bomb/rounds, LoL towers, Dota roshan) for one game_id. Sandbox=30-60s delayed, Hobby=5s delayed, Builder+=real-time."),
    "get_live_odds": (1, "In-play shifting betting odds and active markets (omit game_id to list matches). Hobby+."),
    "get_live_odds_history": (1, "In-play Redis shift log (minutes). Closing ML/totals/spreads: get_lines_history. Hobby+."),
    "get_lines_history": (2, "Opening and closing team mainlines for a match slug / kr_match_id."),
    "get_live_ws": (2, "Live push WebSocket URL + subscribe contract (Builder+). Connect from your app."),
    "get_gamelogs": (0, "Per-map player history for grading, including sport-native model fields when present (up to 5000 maps). Sandbox=last 30 days, Hobby=last 90 days, Builder+=full vault."),
    "get_boxscore": (0, "Finished-match vault boxscore + STARTER/SUB lineup and model fields by slug/kr_match_id — not live KDA. Sandbox=last 30 days, Hobby=last 90 days, Builder+=full vault."),
    "get_match_prep": (2, "CS2, R6, COD, Valorant & Apex team stats, mode/map winrates, map pool/biases, key player matchups, and betting insights (KashRock slug/kr_match_id)."),
    "get_player_board": (2, "CS2 favourite weapons or Valorant agent/role board (KashRock slug/kr_match_id)."),
    "get_tournament_maps": (2, "CS2 tournament maps for a KashRock match slug / kr_match_id."),
    "get_results": (0, "Settled prop grades (hit/miss/push). Sandbox=last 30 days, Hobby=last 90 days, Builder+=full vault."),
    "get_history_tape": (2, "Quote tape for a prop/book over time."),
    "get_team_h2h": (1, "Team head-to-head meetings from the vault."),
    "explain_error": (0, "Turn a 403/401 into plain English."),
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
