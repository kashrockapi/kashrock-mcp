"""KashRock MCP server. Login with Google; tools call the live API."""

from __future__ import annotations

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from mcp.server import MCPServer as FastMCP

from kashrock_mcp.login import run_login
from kashrock_mcp.tools import register_tools

mcp = FastMCP("kashrock")


@mcp.tool()
async def login() -> str:
    """Open Google sign-in in the browser and store a KashRock API key locally."""
    return await run_login()


register_tools(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
