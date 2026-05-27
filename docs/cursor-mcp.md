# Cursor MCP setup

Dogfood AllocContext Tier 1 tools in Cursor.

## Install

```bash
pip install -e ".[mcp]"
```

Ensure ingest has populated a local SQLite DB (`python -m alloccontext ingest`).

## Configure Cursor

Copy [cursor-mcp.example.json](cursor-mcp.example.json) into your Cursor MCP
settings and set absolute paths for `ALLOC_CONTEXT_CONFIG` and
`ALLOC_CONTEXT_DB`.

Or merge this block into `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "alloc-context": {
      "command": "alloc-context",
      "args": ["mcp"],
      "env": {
        "ALLOC_CONTEXT_CONFIG": "/path/to/config/config.yaml"
      }
    }
  }
}
```

Alternative entry point: `alloc-context-mcp` (same stdio server).

## Tools

| Tool | Keys required |
|------|----------------|
| `get_market_context` | Local ingest DB only |
| `get_rebalance_plan` | None (pure math) |
| `check_allocation_band` | None (pure math) |

All responses include `as_of` and `age_seconds`.
