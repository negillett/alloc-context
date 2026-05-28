"""Redact EVM addresses from paid smoke logs (CI-safe output)."""

from __future__ import annotations

import os
import re

_EVM_ADDRESS = re.compile(r"0x[a-fA-F0-9]{40}")


def smoke_log_addresses_enabled() -> bool:
    """When true, print full 0x addresses (local debugging only)."""
    return os.environ.get("SMOKE_LOG_ADDRESSES", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def mask_evm_address(address: str) -> str:
    """Return a shortened address safe for CI logs."""
    value = address.strip()
    if not value.startswith("0x") or len(value) < 10:
        return value
    return f"{value[:6]}…{value[-4:]}"


def redact_evm_addresses(text: str) -> str:
    """Replace EVM addresses in free-form text unless logging is enabled."""
    if smoke_log_addresses_enabled():
        return text

    def _replace(match: re.Match[str]) -> str:
        return mask_evm_address(match.group(0))

    return _EVM_ADDRESS.sub(_replace, text)


def smoke_log(message: str) -> None:
    """Print a line with addresses redacted unless SMOKE_LOG_ADDRESSES is set."""
    print(redact_evm_addresses(message))
