from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from alloccontext.alerts.policy import (
    delivery_allowed,
    evaluate_rebalance_alert,
    record_alert,
)
from alloccontext.rollup.context import build_context_bundle
from alloccontext.rollup.portfolio import build_portfolio_context
from alloccontext.timeutil import utc_now
from alloccontext_operator.deliver.email import email_configured, send_email
from alloccontext_operator.synthesize.allocation_advice import (
    asset_label,
    synthesize_allocation_advice,
)


def _format_alert_body(
    candidate: dict[str, Any],
    config,
    *,
    allocation_advice: str | None = None,
) -> str:
    portfolio = candidate["portfolio"]
    allocation = portfolio.get("allocation_pct") or {}
    target = portfolio.get("target_allocation_pct") or {}
    drift = portfolio.get("drift") or {}
    band = config.portfolio.rebalance_band

    lines = [
        "**Allocation band alert**",
        "",
        f"Trigger: `{candidate['trigger_key']}`",
        f"Hint: `{candidate['hint']}`",
        "",
        f"NAV: ${portfolio.get('nav_usd', 0):,.2f}",
        f"Cash: ${portfolio.get('cash_usd', 0):,.2f}",
        "",
        "Current vs target (pct points drift):",
    ]
    for asset in ("BTC", "ETH", "CASH"):
        cur = allocation.get(asset)
        tgt = target.get(asset)
        d = drift.get(asset)
        if cur is None:
            continue
        lines.append(
            f"- {asset_label(asset)}: {float(cur) * 100:.1f}% "
            f"(target {float(tgt or 0) * 100:.1f}%, drift {float(d or 0) * 100:+.1f})"
        )
    lines.extend(
        [
            "",
            f"Rebalance band: ±{band * 100:.0f}%",
        ]
    )
    if allocation_advice:
        lines.extend(
            [
                "",
                "**Suggested allocation**",
                "",
                allocation_advice.strip(),
            ]
        )
    lines.extend(
        [
            "",
            "Open Kraken to review allocation — no automated trades.",
            "",
            "_Not financial advice._",
        ]
    )
    return "\n".join(lines)


def check_alerts(
    conn: sqlite3.Connection,
    config,
    *,
    email: bool = True,
    stdout: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate alert triggers; email when policy allows."""
    if not config.deliver.alerts.enabled:
        return {"ok": True, "skipped": True, "reason": "alerts_disabled"}

    ts = now or utc_now()
    portfolio = build_portfolio_context(conn, config)
    candidate = evaluate_rebalance_alert(portfolio, config)
    if candidate is None:
        return {"ok": True, "fired": False, "reason": "no_trigger"}

    allowed, block_reason = delivery_allowed(conn, config, candidate, now=ts)
    context = build_context_bundle(
        conn,
        config,
        scope="daily",
        rollup=config.rollup,
        as_of=ts,
    )
    allocation_advice = synthesize_allocation_advice(
        context,
        config,
        hint=str(candidate["hint"]),
    )
    body = _format_alert_body(
        candidate,
        config,
        allocation_advice=allocation_advice,
    )
    delivered_via: str | None = None

    if allowed:
        if stdout:
            print(body)
            delivered_via = "stdout"
        if email and email_configured(config.deliver.email):
            send_email(
                subject="AllocContext — Allocation band alert",
                body=body,
                config=config.deliver.email,
            )
            delivered_via = "email" if delivered_via is None else f"{delivered_via}+email"
        if delivered_via is None:
            record_alert(conn, candidate, delivered_via=None, fired_at=ts)
            return {
                "ok": True,
                "fired": False,
                "suppressed": True,
                "reason": "no_delivery_channel",
                "trigger_key": candidate["trigger_key"],
                "hint": candidate["hint"],
            }
        record_alert(conn, candidate, delivered_via=delivered_via, fired_at=ts)
        return {
            "ok": True,
            "fired": True,
            "delivered_via": delivered_via,
            "trigger_key": candidate["trigger_key"],
            "hint": candidate["hint"],
        }

    record_alert(conn, candidate, delivered_via=None, fired_at=ts)
    return {
        "ok": True,
        "fired": False,
        "suppressed": True,
        "reason": block_reason,
        "trigger_key": candidate["trigger_key"],
        "hint": candidate["hint"],
    }
