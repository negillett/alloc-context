#!/usr/bin/env python3
"""Verify x402 production configuration (CDP facilitator + discovery)."""

from __future__ import annotations

import sys

from alloccontext.x402_production_check import (
    X402ProductionCheckError,
    run_production_checks,
)


def main() -> None:
    try:
        messages = run_production_checks()
    except X402ProductionCheckError as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1) from exc
    for message in messages:
        print(f"OK: {message}")
    print("All production checks passed.")


if __name__ == "__main__":
    main()
