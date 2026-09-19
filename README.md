# kashrock-mcp

<!-- mcp-name: com.kashrock/kashrock-mcp -->

Full tier-scoped KashRock esports MCP for Cursor, Claude, and other agents.

## Install (effortless)

```json
{
  "mcpServers": {
    "kashrock": {
      "command": "uvx",
      "args": ["kashrock-mcp"]
    }
  }
}
```

Then say **log in to KashRock**. Google opens; the agent gets your billed plan.

Requires [uv](https://docs.astral.sh/uv/). Optional: `KASHROCK_API_KEY` skips login.

## Local (this repo)

```bash
cd mcp && uv sync
```

Cursor `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "kashrock": {
      "command": "uv",
      "args": ["run", "--directory", "/ABS/PATH/TO/kashrock/mcp", "kashrock-mcp"],
      "env": { "KASHROCK_API_KEY": "kr_…" }
    }
  }
}
```

## What agents can do

20 tools, each parameterized across all 8 titles and every plan tier:

- **Session**: sign in (`login`), check plan/identity (`get_identity`), reference data + error help + goal-based tool picks (`get_guidance`)
- **Board**: DFS props (`get_props`), DFS+sportsbook named-player props (`get_player_props`), player/team media (`get_media`), team mainlines / cross-venue edges / moneylines (`get_lines`), DFS book-vs-book price gaps (`get_gaps`)
- **Players**: find/fetch a player + stats (`get_player`), leaderboard (`get_rankings`), research slips/tapes (`get_research`)
- **Schedule**: find matches — list, search by team(s), full team schedule, or head-to-head (`get_matches`), live streams (`get_streams`)
- **Match intel** (Builder+): team stats, player weapon/agent board, or CS2 tournament maps, all via `get_match_prep`
- **Live** (Builder+ real-time; Hobby=5s delayed; Sandbox=CS2 REST 30-60s delayed): in-game boxscore/frame/events (`get_live_boxscore`), in-play odds + shift history (`get_live_odds`)
- **History/grading**: full match detail or recent list (`get_boxscore`), per-map player logs (`get_gamelogs`), settled prop grades (`get_results`), opening/closing lines or a prop's quote tape (`get_lines_history`)
- Public ids: lists and boxscores emit `kr_match_id`, `kr_tm_*` teams, `kr_pl_*` players. Lineup includes `STARTER` and `SUB`. Never pass foreign numerics.

Live KDA path: `get_live_boxscore("cs2")` → pick `game_id` → `get_live_boxscore("cs2", game_id)` → add `view="frame"` or `view="events"` for more detail. Sport boards: CS2 money/bomb, LoL gold/towers, Dota gold/roshan when visible, Deadlock gold/CS/level on tournament games. Do not use `get_boxscore` for mid-map stats (that is finished-match vault + lineup + model fields, not live).

Call `get_identity` first, or `get_guidance(mode="build", goal="...")` for a goal-based tool shortlist. Stacks are not exposed.

Docs: https://www.kashrock.com/mcp

App SDKs (not MCP): `pip install kashrock` · [Python](https://github.com/kashrockapi/kashrock-python) · [JS](https://github.com/kashrockapi/kashrock-js)

