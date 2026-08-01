"""MCP server for viparse — ``pip install viparse[mcp]``.

Run it with ``viparse-mcp`` or ``python -m viparse.mcp``.
"""

from __future__ import annotations

from viparse.mcp.server import build_server, main

__all__ = ["build_server", "main"]
