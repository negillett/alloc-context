# Migration from market-analyst

AllocContext was renamed from **market-analyst** (May 2026). New installs use
**alloc-context** + **alloc-context-operator** only.

| Before | After |
|--------|-------|
| Package `analyst/` | `alloccontext/` |
| `python -m analyst` | `python -m alloccontext` |
| CLI `market-analyst` | `alloc-context` |
| `MARKET_ANALYST_*` env | `ALLOC_CONTEXT_*` |
| Default DB `state/analyst.db` | `state/alloccontext.db` |
| systemd `market-analyst-*` | `alloc-context-*` + operator units |
| In-repo briefs/alerts | [alloc-context-operator](https://github.com/negillett/alloc-context-operator) |

## Environment variables

Use **`ALLOC_CONTEXT_*` only**. Legacy `MARKET_ANALYST_CONFIG` and
`MARKET_ANALYST_DB` are no longer read.

| Variable | Purpose |
|----------|---------|
| `ALLOC_CONTEXT_CONFIG` | Path to core `config.yaml` |
| `ALLOC_CONTEXT_DB` | Path to SQLite cache (overrides YAML `paths.db`) |

Example shared host file (`/opt/trading/shared/.env`):

```bash
ALLOC_CONTEXT_CONFIG=/opt/trading/alloc-context/config/config.yaml
ALLOC_CONTEXT_DB=/opt/trading/alloc-context/state/alloccontext.db
```

## Local checkout

```bash
pip install -e ".[dev]"
```

Update scripts and aliases to `python -m alloccontext`.

## Self-hosted deploy

1. Deploy **alloc-context** (ingest + MCP). See [self-hosting.md](self-hosting.md).
2. Deploy **alloc-context-operator** (briefs/alerts via MCP).
3. Remove any leftover `market-analyst` checkout and systemd units.
4. Copy `analyst.db` → `alloccontext.db` once if upgrading an old host, then
   set `ALLOC_CONTEXT_DB` to the new path.

`deploy/remote-install.sh` disables legacy brief/ingest timers from older
installs when present.

## GitHub

Repository renamed to **alloc-context**. Update your remote:

```bash
git remote set-url origin git@github.com:YOUR_ORG/alloc-context.git
```
