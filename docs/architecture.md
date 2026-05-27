# Architecture

## Purpose

**AllocContext** — deterministic market facts, portfolio rollups, and MCP tools
for agents. Exchange APIs and third-party feeds are **data sources only** — no
order placement, no gate authority, no bot shadow modes.

**AllocContext Operator** (separate package) — email briefs, band alerts, and
LLM synthesis for self-hosted operators. See [mcp-roadmap.md](mcp-roadmap.md).

Agent-facing MCP + x402: [mcp-roadmap.md](mcp-roadmap.md).

## Pipeline

```text
┌──────────────────────────────────────────────────────────────────┐
│                    alloc-context (core)                          │
├──────────────────────────────────────────────────────────────────┤
│  ingest/          Scheduled pulls → normalized rows               │
│  store/           SQLite append-only snapshots                    │
│  rollup/          ContextBundle (deterministic, reproducible)     │
│  alerts/          Band evaluation policy (no delivery)            │
│  mcp/             Agent tools + optional x402 HTTP                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│              alloc-context-operator (self-host ops)               │
├──────────────────────────────────────────────────────────────────┤
│  synthesize/      LLM prose from ContextBundle only               │
│  brief/           daily + weekly orchestration                    │
│  deliver/         Email, stdout, archived markdown, alert send    │
│  review/          Monthly forward-watch review                    │
│  predictions/     Forward watches extracted from brief prose      │
└──────────────────────────────────────────────────────────────────┘
```

## Trust boundaries

| Layer | LLM? | Places orders? |
|-------|------|----------------|
| Ingest | No | No |
| Rollup | No | No |
| Synthesize (operator) | Yes (narrative only) | No |
| Deliver (operator) | No | No |
| MCP (core) | No | No |

## Data horizon

One quarterly window (`horizon.days: 90` by default) for everything persisted:
market bars, sentiment history, portfolio snapshots, brief archive rows,
prediction log, and markdown brief files under `state/briefs/`. Rollups and
LLM context should not assume data older than this unless explicitly archived
off-system.

The LLM **never** sees raw API credentials, never calls exchanges, and must
not invent numbers absent from the ContextBundle. Prompts require citing
deltas (“F&G 72 → 68 since prior brief”).

## ContextBundle

JSON document at a point in time. See [context-bundle.md](context-bundle.md).

Sections:

- `portfolio` — Kraken NAV, allocation, drift vs target, P&L windows
- `market` — BTC/ETH OHLC-derived signals
- `sentiment` — Kalshi cluster, F&G, optional breadth
- `macro` — calendar events past 24h / next 7d, ETF flows when enabled
- `delta` — changes since last daily brief

## Daily vs weekly (operator)

| | Daily | Weekly |
|---|--------|--------|
| Focus | Overnight moves, today’s calendar, portfolio drift | Regime recap, what mattered, forward week |
| Length | Short (email-friendly) | Longer synthesis |
| Archive | `state/briefs/daily/YYYY-MM-DD.md` | `state/briefs/weekly/YYYY-Www.md` |

## Alerts (operator)

Optional threshold notifications (allocation band breach) use core rollup +
`alloccontext/alerts/policy.py` for evaluation; delivery lives in
`alloccontext_operator/deliver/alerts.py`. Ingest refreshes data only — a
separate systemd timer runs alerts on schedule.

Scheduled briefs always send; alerts respect cooldowns (`min_hours_between`,
`max_per_7d`, `dedupe_hours`).

Enable in config:

```yaml
deliver:
  alerts:
    enabled: true
    triggers:
      rebalance_band: true
```

The band uses `portfolio.rebalance_band` (default ±15% drift vs target).

## Prediction log (operator)

Daily and weekly briefs include a **Forward watches** section with bullets:

`- IF [condition] | WATCH [what to monitor] | BY [timeframe]`

Parsed watches are stored in `brief_predictions`. Run
`python -m alloccontext_operator review monthly` to score them against current
facts (optional `--apply` to persist LLM scores).

## Optional self-hosting

Linux + systemd timers for scheduled ingest (core) and email briefs/alerts
(operator) are documented in [self-hosting.md](self-hosting.md). Not required
for MCP consumers.

## Non-goals

- Automated trade execution
- Holding user exchange secrets on a shared MCP server (BYOK in request only)
- Backtest / replay engines
- Multi-user SaaS
