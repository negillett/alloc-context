from __future__ import annotations

import pytest

from alloccontext.x402_smoke_redact import (
    mask_evm_address,
    redact_evm_addresses,
    smoke_log_addresses_enabled,
)


def test_mask_evm_address_shortens() -> None:
    addr = "0xC8e3ff2cd32a162027615f00DA7Aa68eF2F35df5"
    assert mask_evm_address(addr) == "0xC8e3…5df5"


def test_redact_evm_addresses_in_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SMOKE_LOG_ADDRESSES", raising=False)
    text = "payer 0xAbCdEf0123456789012345678901234567890AbCd seller"
    assert redact_evm_addresses(text) == "payer 0xAbCd…0AbCd seller"


def test_redact_skipped_when_logging_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMOKE_LOG_ADDRESSES", "1")
    assert smoke_log_addresses_enabled()
    addr = "0xC8e3ff2cd32a162027615f00DA7Aa68eF2F35df5"
    assert redact_evm_addresses(f"payTo {addr}") == f"payTo {addr}"
