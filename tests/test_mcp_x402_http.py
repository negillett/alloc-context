from __future__ import annotations

import base64
import json

import pytest


_BASE_SEPOLIA_USDC = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"


def _payment_required_amount(response, *, asset: str | None = None) -> int:
    header = response.headers.get("PAYMENT-REQUIRED") or response.headers.get(
        "payment-required"
    )
    assert header, "expected PAYMENT-REQUIRED header on 402 response"
    decoded = json.loads(base64.b64decode(header))
    accepts = decoded.get("accepts") or []
    assert accepts, "expected at least one payment option"
    if asset is None:
        return int(accepts[0]["amount"])
    for option in accepts:
        if option.get("asset", "").lower() == asset.lower():
            return int(option["amount"])
    raise AssertionError(f"no accept option for asset {asset!r}")


@pytest.fixture
def x402_client(monkeypatch: pytest.MonkeyPatch):
    pytest.importorskip("x402")
    from starlette.testclient import TestClient

    from alloccontext.mcp.http import build_http_app

    monkeypatch.setenv("X402_PAY_TO", "0x0000000000000000000000000000000000000001")
    monkeypatch.setenv("X402_FACILITATOR_URL", "https://x402.org/facilitator")
    monkeypatch.setenv("X402_NETWORK", "eip155:84532")
    monkeypatch.setenv("ALLOC_CONTEXT_CONFIG", "config/config.example.yaml")
    app = build_http_app(x402=True, config_path="config/config.example.yaml")
    with TestClient(app) as client:
        yield client


def test_x402_unpaid_cached_tool_call_uses_light_price(x402_client) -> None:
    response = x402_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_market_context",
                "arguments": {"scope": "daily", "freshness": "cached"},
            },
        },
        headers={"Accept": "application/json", "Host": "127.0.0.1:8000"},
    )
    assert response.status_code == 402
    assert _payment_required_amount(response, asset=_BASE_SEPOLIA_USDC) == 20_000


def test_x402_unpaid_live_freshness_uses_heavy_price(x402_client) -> None:
    response = x402_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_market_context",
                "arguments": {"scope": "daily", "freshness": "live"},
            },
        },
        headers={"Accept": "application/json", "Host": "127.0.0.1:8000"},
    )
    assert response.status_code == 402
    assert _payment_required_amount(response, asset=_BASE_SEPOLIA_USDC) == 50_000


def test_x402_unpaid_portfolio_tool_uses_heavy_price(x402_client) -> None:
    response = x402_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_portfolio_state",
                "arguments": {"exchange": "kraken"},
            },
        },
        headers={"Accept": "application/json", "Host": "127.0.0.1:8000"},
    )
    assert response.status_code == 402
    assert _payment_required_amount(response, asset=_BASE_SEPOLIA_USDC) == 50_000
