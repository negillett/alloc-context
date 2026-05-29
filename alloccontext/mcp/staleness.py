from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from alloccontext.timeutil import utc_now


def parse_as_of(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def age_seconds(as_of: datetime, *, now: datetime | None = None) -> int:
    ref = now or utc_now()
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    return max(0, int((ref - as_of).total_seconds()))


def with_staleness(payload: dict[str, Any], *, as_of: datetime) -> dict[str, Any]:
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    return {
        "as_of": as_of.replace(microsecond=0).isoformat(),
        "age_seconds": age_seconds(as_of),
        **payload,
    }


def _coerce_as_of(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return parse_as_of(value)
    except ValueError:
        return None


# Bundle blocks that carry a timestamp describing when their underlying data was
# captured (as opposed to when the response was generated).
def oldest_data_as_of(bundle: dict[str, Any]) -> datetime | None:
    """Oldest underlying-data timestamp in a built bundle (worst-case freshness).

    The top-level ``as_of`` is the response generation time, so for cached reads
    it is always ~now even when the underlying portfolio/market data is days old.
    This returns the oldest constituent ``as_of`` (portfolio snapshot, sentiment,
    market breadth) so callers can see the true age of the facts.
    """
    candidates: list[Any] = []
    portfolio = bundle.get("portfolio")
    if isinstance(portfolio, dict):
        candidates.append(portfolio.get("as_of"))
    sentiment = bundle.get("sentiment")
    if isinstance(sentiment, dict):
        candidates.append(sentiment.get("as_of"))
    market = bundle.get("market")
    if isinstance(market, dict):
        breadth = market.get("breadth")
        if isinstance(breadth, dict):
            candidates.append(breadth.get("as_of"))
    # get_market_context surfaces breadth at the top level.
    top_breadth = bundle.get("breadth")
    if isinstance(top_breadth, dict):
        candidates.append(top_breadth.get("as_of"))

    parsed = [dt for dt in (_coerce_as_of(value) for value in candidates) if dt is not None]
    if not parsed:
        return None
    return min(parsed)


def with_data_staleness(
    payload: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Add ``data_as_of`` / ``data_age_seconds`` from the oldest constituent fact.

    Mutates and returns ``payload``. No-op when no constituent timestamp is
    present (e.g. an empty bundle), leaving the response-generation ``as_of``
    untouched.
    """
    oldest = oldest_data_as_of(payload)
    if oldest is None:
        return payload
    payload["data_as_of"] = oldest.replace(microsecond=0).isoformat()
    payload["data_age_seconds"] = age_seconds(oldest, now=now)
    return payload
