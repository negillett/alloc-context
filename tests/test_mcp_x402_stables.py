from __future__ import annotations

import pytest

from alloccontext.mcp.x402_config import MCP_HTTP_PATH, build_x402_routes, X402Settings
from alloccontext.mcp.x402_stables import (
    BASE_MAINNET,
    BASE_SEPOLIA,
    FALLBACK_ACCEPTED_STABLES,
    dollar_to_atomic,
    effective_accepted_stable_symbols,
    load_accepted_stable_symbols,
    parse_accepted_stable_symbols,
    stables_for_network,
)


def test_parse_accepted_stable_symbols() -> None:
    assert parse_accepted_stable_symbols("usdc, eurc") == ("USDC", "EURC")
    assert parse_accepted_stable_symbols("") == ()


def test_effective_accepted_stable_symbols_empty_falls_back_to_usdc() -> None:
    assert effective_accepted_stable_symbols(()) == FALLBACK_ACCEPTED_STABLES


def test_empty_env_stables_match_routes_and_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("X402_ACCEPTED_STABLES", "")
    assert load_accepted_stable_symbols() == FALLBACK_ACCEPTED_STABLES
    settings = X402Settings(
        enabled=True,
        pay_to="0xSeller",
        facilitator_url="https://x402.org/facilitator",
        network=BASE_MAINNET,
        mcp_price="$0.02",
        mcp_path=MCP_HTTP_PATH,
        accepted_stables=(),
    )
    route = build_x402_routes(settings)[f"POST {MCP_HTTP_PATH}"]
    assert len(route.accepts) == 1


def test_dollar_to_atomic_six_decimals() -> None:
    assert dollar_to_atomic("$0.02", 6) == "20000"
    assert dollar_to_atomic("$0.05", 6) == "50000"


def test_mainnet_lists_usdc_and_eurc_by_default() -> None:
    stables = stables_for_network(BASE_MAINNET)
    assert [s.symbol for s in stables] == ["USDC", "EURC"]


def test_sepolia_filters_to_usdc_only() -> None:
    stables = stables_for_network(BASE_SEPOLIA)
    assert [s.symbol for s in stables] == ["USDC"]


def test_build_x402_routes_mainnet_has_two_accepts() -> None:
    settings = X402Settings(
        enabled=True,
        pay_to="0xSeller",
        facilitator_url="https://x402.org/facilitator",
        network=BASE_MAINNET,
        mcp_price="$0.02",
        mcp_path=MCP_HTTP_PATH,
        accepted_stables=("USDC", "EURC"),
    )
    route = build_x402_routes(settings)[f"POST {MCP_HTTP_PATH}"]
    assert len(route.accepts) == 2
    assert all(opt.scheme == "exact" for opt in route.accepts)
    assert all(opt.pay_to == "0xSeller" for opt in route.accepts)


def test_build_x402_routes_sepolia_single_accept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("X402_ACCEPTED_STABLES", raising=False)
    settings = X402Settings(
        enabled=True,
        pay_to="0xSeller",
        facilitator_url="https://x402.org/facilitator",
        network=BASE_SEPOLIA,
        mcp_price="$0.02",
        mcp_path=MCP_HTTP_PATH,
        accepted_stables=parse_accepted_stable_symbols(None),
    )
    route = build_x402_routes(settings)[f"POST {MCP_HTTP_PATH}"]
    assert len(route.accepts) == 1
