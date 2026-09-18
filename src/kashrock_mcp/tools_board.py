"""Board tools: props, moneylines, consensus lines, coverage, media, snapshots."""

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
        book: str = "",
        player: str = "",
        market: str = "",
        market_contains: str = "",
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
        slim: bool = True,
    ) -> Any:
        """DFS player props only. Prefer book/market/player filters — default slim+limit keeps payloads small."""
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
        """DFS + sportsbook named-player props. Default view=groups + slim — not the full 8MB dump."""
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
        return ok(
            {
                "board": data.get("board"),
                "groups": groups,
                "books": data.get("books"),
                "fetched_at": data.get("generated_at"),
            },
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
    async def get_moneylines(
        sport: str,
        book: str = "",
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> Any:
        """Team match moneylines from consensus lines board (not DFS props). Upcoming only by default."""
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
            hint="For full consensus use get_lines; top edges use get_best_lines.",
        )

    @mcp.tool()
    async def get_lines(
        sport: str,
        market: str = "",
        event_id: str = "",
        live_only: bool = True,
    ) -> Any:
        """Consensus mainlines across sportsbooks, DFS Teams, and prediction markets (Hobby+). live_only=true (default) drops started matches."""
        params: Dict[str, Any] = {"live_only": str(bool(live_only)).lower()}
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
    async def get_best_lines(
        sport: str, market: str = "", limit: int = 25, live_only: bool = True
    ) -> Any:
        """Top cross-venue edges from /lines (useful operation — not raw board dump). live_only=true (default) drops started matches."""
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
        """DFS book-vs-book line spreads for the same player/event/market (Hobby+)."""
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
    async def get_coverage(sport: str) -> Any:
        """How many props each book has on the live board for a sport."""
        data = await api_get(
            f"/v6/esports/{sport}/props",
            {"include_props": "false"},
        )
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

    @mcp.tool()
    async def get_media(
        sport: str,
        player: str = "",
        player_id: int = 0,
        team: str = "",
        team_id: int = 0,
        opponent: str = "",
    ) -> Any:
        """Resolve player faces + team logos. Same links shape as props (player_image, team_logo)."""
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

    @mcp.tool()
    async def get_player_snapshot(
        sport: str,
        player: str,
        board: str = "all",
        market_contains: str = "",
        limit: int = DEFAULT_LIMIT,
    ) -> Any:
        """One-shot: media links + slim player-prop groups for a player (agent-friendly)."""
        media = await api_get(
            f"/v6/esports/{sport}/media",
            {"player": player},
        )
        params: Dict[str, Any] = {
            "board": board or "all",
            "player": player,
            "view": "groups",
            "slim": "true",
            "limit": _clamp_limit(limit),
            "offset": 0,
        }
        if market_contains:
            params["market_contains"] = market_contains
        props = await api_get(f"/v6/esports/{sport}/player-props", params)
        if isinstance(media, dict) and media.get("ok") is False:
            return media
        if isinstance(props, dict) and props.get("ok") is False:
            return props
        groups = list((props or {}).get("groups") or []) if isinstance(props, dict) else []
        return ok(
            {
                "media": media if isinstance(media, dict) else {},
                "groups": groups,
                "books": (props or {}).get("books") if isinstance(props, dict) else [],
            },
            sport=sport,
            total=(props or {}).get("total_groups", len(groups)) if isinstance(props, dict) else len(groups),
            returned=len(groups),
            filters={"player": player, "board": board, "market_contains": market_contains},
        )
