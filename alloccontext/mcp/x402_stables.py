"""Base stablecoin options for x402 exact payments."""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from alloccontext.mcp.x402_pricing import (
    build_mcp_dynamic_price,
    mcp_call_is_heavy,
    read_mcp_request_json,
)

BASE_MAINNET = "eip155:8453"
BASE_SEPOLIA = "eip155:84532"
DEFAULT_ACCEPTED_STABLES = "USDC,EURC"


@dataclass(frozen=True)
class StableCoin:
    """ERC-20 stable accepted for x402 exact settlement on Base."""

    symbol: str
    address: str
    decimals: int
    eip712_name: str
    eip712_version: str


# Circle USDC on Base mainnet matches x402 NETWORK_CONFIGS default_asset.
_BASE_MAINNET_STABLES: dict[str, StableCoin] = {
    "USDC": StableCoin(
        symbol="USDC",
        address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        decimals=6,
        eip712_name="USD Coin",
        eip712_version="2",
    ),
    "EURC": StableCoin(
        symbol="EURC",
        address="0x60a3E35Cc302bFA44Cb288Bc5a4F316Fdb1adb42",
        decimals=6,
        eip712_name="EURC",
        eip712_version="2",
    ),
}

_BASE_SEPOLIA_STABLES: dict[str, StableCoin] = {
    "USDC": StableCoin(
        symbol="USDC",
        address="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        decimals=6,
        eip712_name="USDC",
        eip712_version="2",
    ),
}

_STABLES_BY_NETWORK: dict[str, dict[str, StableCoin]] = {
    BASE_MAINNET: _BASE_MAINNET_STABLES,
    BASE_SEPOLIA: _BASE_SEPOLIA_STABLES,
}


def parse_accepted_stable_symbols(raw: str | None) -> tuple[str, ...]:
    """Parse comma-separated stable symbols (e.g. USDC,EURC)."""
    value = (raw if raw is not None else DEFAULT_ACCEPTED_STABLES).strip()
    if not value:
        return ()
    return tuple(part.strip().upper() for part in value.split(",") if part.strip())


def load_accepted_stable_symbols() -> tuple[str, ...]:
    return parse_accepted_stable_symbols(os.environ.get("X402_ACCEPTED_STABLES"))


def stables_for_network(
    network: str,
    symbols: tuple[str, ...] | None = None,
) -> tuple[StableCoin, ...]:
    """Return configured stablecoins for a CAIP-2 network."""
    catalog = _STABLES_BY_NETWORK.get(network)
    if catalog is None:
        return ()

    chosen = symbols if symbols is not None else load_accepted_stable_symbols()
    if not chosen:
        return ()

    resolved: list[StableCoin] = []
    for symbol in chosen:
        stable = catalog.get(symbol)
        if stable is not None:
            resolved.append(stable)
    if chosen and not resolved:
        raise ValueError(
            f"no accepted stables from {chosen!r} are listed on network {network}"
        )
    return tuple(resolved)


def dollar_to_atomic(amount: str, decimals: int) -> str:
    """Convert a $ price string to ERC-20 atomic units (USD-pegged stables)."""
    dollars = Decimal(amount.strip().lstrip("$"))
    scale = Decimal(10) ** decimals
    atomic = (dollars * scale).to_integral_value(rounding=ROUND_HALF_UP)
    return str(int(atomic))


def build_stable_dynamic_price(
    *,
    stable: StableCoin,
    light_price: str,
    heavy_price: str,
):
    """Build async DynamicPrice returning AssetAmount for one stable."""

    async def resolve_price(context):
        body = await read_mcp_request_json(context)
        price_str = heavy_price if mcp_call_is_heavy(body) else light_price
        return {
            "amount": dollar_to_atomic(price_str, stable.decimals),
            "asset": stable.address,
            "extra": {
                "name": stable.eip712_name,
                "version": stable.eip712_version,
            },
        }

    return resolve_price


def build_payment_options_for_stables(
    *,
    pay_to: str,
    network: str,
    light_price: str,
    heavy_price: str,
    symbols: tuple[str, ...] | None = None,
):
    """PaymentOption list: one per accepted stable; fallback to $ price on unknown nets."""
    from x402.http.types import PaymentOption

    stables = stables_for_network(network, symbols)
    if not stables:
        return [
            PaymentOption(
                scheme="exact",
                pay_to=pay_to,
                price=build_mcp_dynamic_price(
                    light_price=light_price,
                    heavy_price=heavy_price,
                ),
                network=network,
            )
        ]

    return [
        PaymentOption(
            scheme="exact",
            pay_to=pay_to,
            price=build_stable_dynamic_price(
                stable=stable,
                light_price=light_price,
                heavy_price=heavy_price,
            ),
            network=network,
        )
        for stable in stables
    ]
