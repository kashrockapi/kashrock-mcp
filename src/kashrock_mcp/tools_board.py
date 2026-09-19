"""Board tools: props, consensus lines, gaps, media."""

from __future__ import annotations

from typing import Any, Dict, List

from kashrock_mcp.http import api_get, ok

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


def _book_name(row: Dict[str, Any]) -> str:
    return str(
        row.get("sportsbook_name")
        or row.get("book")
        or row.get("book_key")
        or ""
    ).lower()


def _player_name(row: Dict[str, Any]) -> str:
    return str(row.get("player_name") or row.get("player") or "").lower()


def _clamp_limit(limit: int) -> int:
    try:
        n = int(limit)
    except (TypeError, ValueError):
        n = DEFAULT_LIMIT
    return max(1, min(n, MAX_LIMIT))


def _page(rows: List[Dict[str, Any]], *, limit: int, offset: int = 0) -> Dict[str, Any]:
    lim = _clamp_limit(limit)
    off = max(0, int(offset or 0))
    slice_ = rows[off : off + lim]
    return {
        "total": len(rows),
        "returned": len(slice_),
        "offset": off,
        "limit": lim,
        "has_more": off + lim < len(rows),
        "rows": slice_,
    }


def register_board(mcp: Any) -> None:
    @mcp.tool()
    async def get_props(
        sport: str,
        coverage_only: bool = False,
        book: str = "",
        player: str = "",
        market: str = "",
        market_contains: str = "",
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
        slim: bool = True,
    ) -> Any:
        """DFS player props only, or per-book coverage counts. Use get_player_props for
        named-sportsbook props; get_lines for team mainlines; get_gaps for the same
        prop priced differently across books.

        Params:
          sport (str, e.g. "cs2"): required.
          coverage_only (bool, e.g. false): true returns per-book prop counts/freshness
            with no prop rows — skips book/player/market/market_contains/limit/offset/slim below.
          book (str, e.g. "prizepicks"): filter to one DFS book.
          player (str, e.g. "s1mple"): substring filter on player name.
          market (str, e.g. "CS2_KILLS_MAP_1"): exact stat_type filter.
          market_contains (str, e.g. "KILLS"): substring stat_type filter.
          limit (int, e.g. 50): row cap, max 200.
          offset (int, e.g. 0): pagination offset.
          slim (bool, e.g. true): default true keeps payloads small.

        Returns: {props:[...], books, board, fetched_at}, or with coverage_only,
        {books: {book_name: {count, note}}}.
        """
        if coverage_only:
            data = await api_get(f"/v6/esports/{sport}/props", {"include_props": "false"})
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            if not isinstance(data, dict):
                return data
            if data.get("books"):
                return ok(
                    {
                        "books": {
                            str(row.get("book")): {
                                "count": row.get("prop_count") or 0,
                                "note": row.get("note"),
                            }
                            for row in data["books"]
                            if isinstance(row, dict)
                        }
                    },
                    sport=sport,
                    total=data.get("total") or 0,
                )
            return ok({"books": {}}, sport=sport, total=0)

        params: Dict[str, Any] = {
            "limit": _clamp_limit(limit),
            "offset": max(0, int(offset or 0)),
            "slim": "true" if slim else "false",
        }
        if book:
            params["book"] = book
        if market:
            params["market"] = market
        if market_contains:
            params["market_contains"] = market_contains
        data = await api_get(f"/v6/esports/{sport}/props", params)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        if not isinstance(data, dict) or "props" not in data:
            return data
        rows = list(data.get("props") or [])
        # Client page only when API ignored limit (pre-deploy hosts).
        if data.get("limit") is None and (limit or offset):
            if player:
                needle = player.lower()
                rows = [r for r in rows if needle in _player_name(r)]
            page = _page(rows, limit=limit, offset=offset)
            rows = page["rows"]
            total, returned, has_more = page["total"], page["returned"], page["has_more"]
            off, lim = page["offset"], page["limit"]
        else:
            if player:
                needle = player.lower()
                rows = [r for r in rows if needle in _player_name(r)]
            total = data.get("total", len(rows))
            returned = data.get("returned", len(rows))
            has_more = bool(data.get("has_more"))
            off = data.get("offset", offset)
            lim = data.get("limit", _clamp_limit(limit))
        hint = None
        if has_more:
            hint = "Narrow with book/market/player or raise offset."
        return ok(
            {
                "props": rows,
                "books": data.get("books"),
                "board": data.get("board") or "dfs",
                "fetched_at": data.get("fetched_at") or data.get("generated_at"),
            },
            sport=sport,
            total=total,
            returned=returned,
            filters={
                "book": book,
                "player": player,
                "market": market,
                "market_contains": market_contains,
                "offset": off,
                "limit": lim,
                "slim": slim,
                "has_more": has_more,
            },
            hint=hint,
        )

    @mcp.tool()
    async def get_player_props(
        sport: str,
        board: str = "all",
        include_media: bool = False,
        book: str = "",
        player: str = "",
        player_id: int = 0,
        market: str = "",
        market_contains: str = "",
        event_id: str = "",
        include_event_lines: bool = False,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
        slim: bool = True,
        view: str = "groups",
    ) -> Any:
        """DFS + sportsbook named-player props. Use get_props for anonymous DFS-only
        props; get_lines for team mainlines; get_gaps for the same prop priced
        differently across books.

        Params:
          sport (str, e.g. "cs2"): required.
          board (str, e.g. "all"): dfs | main | all.
          include_media (bool, e.g. true): with player set, attaches media.player_image
            / media.team_logo for that player in one call instead of a separate get_media call.
          book (str, e.g. "pinnacle"): filter to one book.
          player (str, e.g. "s1mple"): filter to one named player.
          player_id (int, e.g. 12345): filter by numeric provider-linked player id.
          market (str, e.g. "CS2_KILLS_MAP_1"): exact stat_type filter.
          market_contains (str, e.g. "KILLS"): substring stat_type filter.
          event_id (str, e.g. "kr_cs2_evt_123"): filter to one event.
          include_event_lines (bool, e.g. false): attach per-event line context.
          limit (int, e.g. 50): row cap, max 200.
          offset (int, e.g. 0): pagination offset.
          slim (bool, e.g. true): default true keeps payloads small.
          view (str, e.g. "groups"): groups (default, grouped by player/market) | full.

        Returns: {board, groups:[...], books, media?} — groups is the default (slim+limit) shape.
        """
        params: Dict[str, Any] = {
            "board": board or "all",
            "view": view or "groups",
            "slim": "true" if slim else "false",
            "limit": _clamp_limit(limit),
            "offset": max(0, int(offset or 0)),
        }
        if book:
            params["book"] = book
        if player:
            params["player"] = player
        if player_id:
            params["player_id"] = player_id
        if market:
            params["market"] = market
        if market_contains:
            params["market_contains"] = market_contains
        if event_id:
            params["event_id"] = event_id
        if include_event_lines:
            params["include_event_lines"] = "true"
        data = await api_get(f"/v6/esports/{sport}/player-props", params)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        if not isinstance(data, dict):
            return data
        groups = list(data.get("groups") or [])
        if data.get("limit") is None:
            page = _page(groups, limit=limit, offset=offset)
            groups = page["rows"]
            total, returned, has_more = page["total"], page["returned"], page["has_more"]
        else:
            total = data.get("total_groups", data.get("total", len(groups)))
            returned = data.get("returned", len(groups))
            has_more = bool(data.get("has_more"))
        result: Dict[str, Any] = {
            "board": data.get("board"),
            "groups": groups,
            "books": data.get("books"),
            "fetched_at": data.get("generated_at"),
        }
        if include_media and player:
            media = await api_get(f"/v6/esports/{sport}/media", {"player": player})
            if not (isinstance(media, dict) and media.get("ok") is False):
                result["media"] = media
        return ok(
            result,
            sport=sport,
            total=total,
            returned=returned,
            filters={
                "board": board,
                "book": book,
                "player": player,
                "market": market,
                "market_contains": market_contains,
                "event_id": event_id,
                "view": view,
                "slim": slim,
                "offset": data.get("offset", offset),
                "has_more": has_more,
            },
        )

    @mcp.tool()
    async def get_lines(
        sport: str,
        view: str = "consensus",
        market: str = "",
        event_id: str = "",
        book: str = "",
        live_only: bool = True,
        limit: int = 25,
        offset: int = 0,
    ) -> Any:
        """Team mainlines: full consensus, top cross-venue edges, or flattened
        moneylines — all from the same lines board. Use get_props/get_player_props for
        player props, not this tool; use get_gaps for cross-book price gaps on the
        same DFS prop.

        Params:
          sport (str, e.g. "cs2"): required.
          view (str, e.g. "consensus"): consensus (default; full events/markets/outcomes
            across sportsbooks, DFS Teams, and prediction markets) | best_edges (top
            cross-venue consensus edges only) | moneyline (flattened book/team/odds rows,
            forced to market=match_winner).
          market (str, e.g. "match_winner"): view=consensus/best_edges filter; ignored for moneyline.
          event_id (str, e.g. "kr_cs2_evt_123"): view=consensus only — one event.
          book (str, e.g. "pinnacle"): view=moneyline only — filter to one book.
          live_only (bool, e.g. true): default true drops started matches (consensus/best_edges/moneyline).
          limit (int, e.g. 25): view=best_edges/moneyline row cap, max 200.
          offset (int, e.g. 0): view=moneyline pagination offset.

        Returns: consensus -> {events:[...]}; best_edges -> {top_edges:[...]}; moneyline -> {moneylines:[...]}.
        Hobby+.
        """
        v = (view or "consensus").strip().lower()

        if v == "moneyline":
            data = await api_get(
                f"/v6/esports/{sport}/lines",
                {"market": "match_winner", "live_only": "true"},
            )
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            events = list((data or {}).get("events") or []) if isinstance(data, dict) else []
            rows: List[Dict[str, Any]] = []
            for ev in events:
                for mkt in ev.get("markets") or []:
                    for outcome in mkt.get("outcomes") or []:
                        for src in outcome.get("sources") or []:
                            key = str(src.get("source") or "").lower()
                            if book and book.lower() not in key:
                                continue
                            rows.append(
                                {
                                    "book": key,
                                    "stat_type": "MONEYLINE",
                                    "team": outcome.get("name"),
                                    "home_team": ev.get("home_team"),
                                    "away_team": ev.get("away_team"),
                                    "odds": src.get("american"),
                                    "probability": src.get("probability"),
                                    "event_id": ev.get("event_id"),
                                    "event_time": ev.get("event_time"),
                                    "market": mkt.get("market"),
                                }
                            )
            page = _page(rows, limit=limit, offset=offset)
            return ok(
                {"moneylines": page["rows"]},
                sport=sport,
                total=page["total"],
                returned=page["returned"],
                filters={
                    "book": book,
                    "offset": page["offset"],
                    "limit": page["limit"],
                    "has_more": page["has_more"],
                },
                hint="For full consensus use view=consensus; top edges use view=best_edges.",
            )

        if v == "best_edges":
            params: Dict[str, Any] = {"live_only": str(bool(live_only)).lower()}
            if market:
                params["market"] = market
            data = await api_get(f"/v6/esports/{sport}/lines", params or None)
            if isinstance(data, dict) and data.get("ok") is False:
                return data
            edges = list((data or {}).get("top_edges") or []) if isinstance(data, dict) else []
            page = _page(edges, limit=limit, offset=0)
            return ok(
                {"top_edges": page["rows"], "pm_weight": (data or {}).get("pm_weight")},
                sport=sport,
                total=page["total"],
                returned=page["returned"],
                filters={"market": market or "all", "limit": page["limit"]},
                hint="Model-driven edges are internal only. This is venue consensus edges only.",
            )

        # consensus (default)
        params = {"live_only": str(bool(live_only)).lower()}
        if market:
            params["market"] = market
        if event_id:
            params["event_id"] = event_id
        data = await api_get(f"/v6/esports/{sport}/lines", params or None)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        events = list((data or {}).get("events") or []) if isinstance(data, dict) else []
        return ok(
            data,
            sport=sport,
            total=len(events),
            returned=len(events),
            filters={"market": market or "all", "live_only": bool(live_only)},
            hint="Outcomes live under events[].markets[].outcomes — not a props array.",
        )

    @mcp.tool()
    async def get_gaps(
        sport: str,
        min_gap: float = 0.5,
        player: str = "",
        market: str = "",
        market_contains: str = "",
        book: str = "",
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> Any:
        """DFS book-vs-book line spreads for the same player/event/market. Not team
        mainlines (get_lines) and not model edges.

        Params:
          sport (str, e.g. "cs2"): required.
          min_gap (float, e.g. 0.5): minimum line_max−line_min spread to include.
          player (str, e.g. "s1mple"): filter to one player.
          market (str, e.g. "CS2_KILLS_MAP_1"): exact stat_type filter.
          market_contains (str, e.g. "KILLS"): substring stat_type filter.
          book (str, e.g. "prizepicks"): filter to one book.
          limit (int, e.g. 50): row cap, max 200.
          offset (int, e.g. 0): pagination offset.

        Returns: {gaps:[...]} — each row's line_gap = line_max − line_min across DFS books.
        Hobby+.
        """
        params: Dict[str, Any] = {
            "min_gap": min_gap,
            "limit": _clamp_limit(limit),
            "offset": max(0, int(offset or 0)),
        }
        if player:
            params["player"] = player
        if market:
            params["market"] = market
        if market_contains:
            params["market_contains"] = market_contains
        if book:
            params["book"] = book
        data = await api_get(f"/v6/esports/{sport}/gaps", params)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        if not isinstance(data, dict):
            return data
        gaps = list(data.get("gaps") or [])
        return ok(
            data,
            sport=sport,
            total=data.get("total", len(gaps)),
            returned=data.get("returned", len(gaps)),
            filters={
                "min_gap": min_gap,
                "player": player,
                "market": market,
                "market_contains": market_contains,
                "book": book,
                "offset": data.get("offset", offset),
                "limit": data.get("limit", limit),
                "has_more": data.get("has_more", False),
            },
            hint="line_gap = line_max − line_min across DFS books. Not model edges.",
        )

    @mcp.tool()
    async def get_media(
        sport: str,
        player: str = "",
        player_id: int = 0,
        team: str = "",
        team_id: int = 0,
        opponent: str = "",
    ) -> Any:
        """Resolve player faces + team logos by name or id. Standalone because it also
        resolves team-only/opponent lookups with no prop context — for a one-shot
        player-props-plus-media call use get_player_props(include_media=true) instead.

        Params:
          sport (str, e.g. "cs2"): required.
          player (str, e.g. "s1mple"): player name.
          player_id (int, e.g. 12345): numeric provider-linked player id.
          team (str, e.g. "Natus Vincere"): team name.
          team_id (int, e.g. 678): numeric provider-linked team id.
          opponent (str, e.g. "FaZe Clan"): opponent team name, for matchup-scoped lookups.

        Returns: {player_image?, team_logo?, ...} — same links shape used in get_props rows.
        """
        params: Dict[str, Any] = {}
        if player:
            params["player"] = player
        if player_id:
            params["player_id"] = player_id
        if team:
            params["team"] = team
        if team_id:
            params["team_id"] = team_id
        if opponent:
            params["opponent"] = opponent
        data = await api_get(f"/v6/esports/{sport}/media", params or None)
        if isinstance(data, dict) and data.get("ok") is False:
            return data
        return ok(data, sport=sport)
