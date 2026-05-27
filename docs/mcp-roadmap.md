# MCP + x402 roadmap

AllocContext is becoming an **agent-native allocation context API**: structured
facts and rebalance math, discoverable via the x402 Bazaar, paid per call.

Email briefs and optional self-host ingest remain an operator path. MCP is the
product path.

## Product split

| Surface | Audience | Status |
|---------|----------|--------|
| CLI + systemd ingest | Operator self-host | Shipped |
| Email briefs + band alerts | Operator self-host | Shipped |
| **MCP server `alloc-context`** | Agents + developers | Shipped (stdio, Tier 1) |
| **x402 paywall** | Agent wallets | Phase B |
| **Bazaar listing** | Discovery | Phase C |
| **Multi-exchange + BYOK portfolio** | Agents with exchange keys | Phase D |
| **Optional BYOLLM narrative** | Agents with LLM keys | Phase D |

## MCP tools

### Tier 1 — no user keys (public context + math)

| Tool | Input | Output |
|------|-------|--------|
| `get_market_context` | `scope` (daily/weekly) | ContextBundle subset: sentiment, macro, ETF, breadth, `as_of`, `age_seconds` |
| `get_rebalance_plan` | `allocation_pct`, `target_pct`, `nav_usd` | USD deltas + exchange-style move lines |
| `check_allocation_band` | `allocation_pct`, `target_pct`, `band` | `hint`, drift, `outside_band` |

Shipped on stdio (Phase A). Cached context comes from operator ingest DB on
self-host; hosted Phase B serves the same facts from server-side cache.

### Tier 2 — BYOK live portfolio (Phase D)

| Tool | Input | Output |
|------|-------|--------|
| `get_portfolio_state` | `exchange`, read-only credentials in request | Portfolio slice of ContextBundle: NAV, allocation, drift |

Credentials are **pass-through only** — never stored server-side. Initial
exchanges: **Kraken** (existing ingest) and **Coinbase** (Advanced Trade
read-only). Unified response shape regardless of exchange.

### Tier 3 — optional BYOLLM narrative (Phase D)

| Tool / flag | Input | Output |
|-------------|-------|--------|
| `with_narrative=true` on context/brief tools | User LLM API key in request (OpenAI-compatible) | Facts JSON + generated prose |

Default paid path stays **facts only, no LLM**. Narrative is opt-in; user pays
their LLM provider directly. Agent host models can also narrate Tier 1 JSON
without calling this path.

## x402 + Bazaar

1. HTTP/MCP middleware returns `402 Payment Required` with USDC price on Base.
2. Register routes with **Bazaar extension** metadata (semantic description for
   agent search).
3. List on CDP facilitator / Agent.market.

Target pricing (initial): **$0.01–0.05/call** Tier 1; **$0.05–0.10** Tier 2
live portfolio (per exchange).

Bazaar title:

> AllocContext — BTC/ETH allocation drift, rebalance moves & market context

## Implementation phases

### Phase A — MCP skeleton (no payment) ✅

- [x] `alloccontext/mcp/` module — MCP server over stdio
- [x] Wire Tier 1 tools to existing rollup + `rebalance.py`
- [x] JSON schemas + `as_of` / `age_seconds` on every response
- [x] Local Cursor config for dogfooding

### Phase B — x402 gate

- [ ] HTTP / streamable transport for MCP (alongside stdio)
- [ ] x402 middleware on paid routes
- [ ] CDP facilitator + seller wallet
- [ ] Staleness tiers: cached vs on-demand refresh for paid `live` calls

### Phase C — Discovery

- [ ] Bazaar metadata on all paid routes
- [ ] Listing copy optimized for agent semantic search
- [ ] Dogfood via `x402-discovery-mcp` in Cursor

### Phase D — Personalization & multi-exchange

**Exchange & portfolio**

- [ ] Exchange abstraction in ingest + rollup (`kraken`, `coinbase` first)
- [ ] Coinbase Advanced Trade read-only: balances, spot positions, USD NAV
- [ ] MCP `exchange` parameter on portfolio and rebalance tools
- [ ] `get_portfolio_state` Tier 2 BYOK (credentials in request, never stored)
- [ ] Exchange-specific move-line wording (Kraken vs Coinbase order semantics)

**Asset & target configuration**

- [ ] Per-request `assets` filter (default `BTC`, `ETH`; allocation universe
      remains BTC/ETH/CASH until expanded deliberately)
- [ ] Per-request `target_pct` / `band` (already on math tools; document as
      first-class MCP contract)
- [ ] Optional server defaults via config for operator self-host

**BYOLLM (optional)**

- [ ] `with_narrative` flag on selected tools
- [ ] Pass-through LLM key + model in request; reuse `synthesize/` prompts
- [ ] Clear separation: base x402 price = facts; narrative = user’s LLM cost

**Suggested PR slices**

1. `exchange` config schema + Kraken refactor (no new exchange yet)
2. Coinbase ingest + portfolio adapter
3. MCP Tier 2 BYOK + `exchange` param
4. BYOLLM opt-in path

## Non-goals

**Through Phase C (public v1)**

- Holding user exchange or LLM secrets server-side
- LLM on the default paid call path
- More than BTC/ETH/CASH in allocation math (Phase D keeps this unless explicitly expanded)

**Explicitly in scope for Phase D**

- Multi-exchange **live** portfolio via BYOK (Kraken + Coinbase first)
- Optional BYOLLM on opt-in tools only

**Still out of scope (for now)**

- Automated trade execution
- Server-hosted custody or Agentic Wallets integration
- Exotic asset universes (altcoins, perps, staking positions beyond spot cash/crypto split)
- Every exchange — prove Kraken + Coinbase adapter pattern first

## Repo layout (evolving)

```text
alloccontext/
  mcp/
    server.py       # MCP tool definitions
    handlers.py     # tool implementations
  ingest/
    kraken_*.py     # today
    coinbase_*.py   # Phase D
    exchange/       # shared portfolio + OHLC interface (Phase D)
  rollup/
    portfolio.py    # exchange-agnostic portfolio context
  synthesize/       # BYOLLM reuse in Phase D
```

See [context-bundle.md](context-bundle.md) for the facts schema MCP tools expose.
