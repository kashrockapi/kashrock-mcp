# kashrock-mcp

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

- Board: DFS props (`get_props`), DFS+sportsbook player props (`get_player_props`), media (`get_media`), player snapshot (`get_player_snapshot`), consensus lines including DFS Teams (`get_lines` / `get_best_lines`), gaps (`get_gaps`)
- Players / research / rankings / streams / H2H
- Builder+: matches, **live in-game** (`get_live_boxscore` / `get_live_games` / `get_live_frame` / `get_live_odds` / `get_live_odds_history`), **live WebSocket** (`get_live_ws` → `WS /v6/esports/live/ws`), gamelogs, finished vault boxscores (`get_boxscore`), results, history tape, closing mainlines (`get_lines_history`)
- Match intel: `get_match_prep` (CS2, R6, COD, Valorant & Apex team stats, mode/map winrates, map pool/biases, key player matchups, betting insights), `get_player_board` (CS2 weapons / Valorant agents), `get_tournament_maps` — pass KashRock slug/`kr_match_id` only
- Public ids: lists and boxscores emit `kr_match_id`, `kr_tm_*` teams, `kr_pl_*` players. Lineup includes `STARTER` and `SUB`. Never pass foreign numerics.

Live KDA path: `get_live_boxscore("cs2")` → pick `game_id` → `get_live_boxscore("cs2", game_id)`. Sport boards: CS2 money/bomb, LoL gold/towers, Dota gold/roshan when visible, Deadlock gold/CS/level on tournament games. Do not use `get_boxscore` for mid-map stats (that is finished-match vault + lineup + model fields).

Live WebSocket (Builder+): call `get_live_ws` for the `wss://…/v6/esports/live/ws` URL + subscribe ops. Auth with your API key (`?api_key=` / Bearer / `x-api-key`). After `hello`, send `{"op":"subscribe","sport":"cs2","game_id":"<id>|*" }`. Pushes: snapshot, games_list, frame, boxscore, meta, event, odds. WS traffic does not count against HTTP req/min. MCP returns the contract only — your app holds the socket.

Call `whoami`, `list_capabilities`, or `suggest_build` first. Stacks are not exposed.

Docs: https://www.kashrock.com/mcp

App SDKs (not MCP): `pip install kashrock` · [Python](https://github.com/kashrockapi/kashrock-python) · [JS](https://github.com/kashrockapi/kashrock-js)

