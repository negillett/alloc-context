from __future__ import annotations

import urllib.error
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_REDACTED_PARAMS = frozenset(
    {
        "token",
        "apikey",
        "api_key",
    }
)


def redact_url_secrets(url: str) -> str:
    """Remove common API key query params before logging or error text."""
    parsed = urlparse(url)
    if not parsed.query:
        return url
    query = [
        (key, "***" if key.lower() in _REDACTED_PARAMS else value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    return urlunparse(parsed._replace(query=urlencode(query)))


def http_error_message(exc: urllib.error.HTTPError, *, context: str) -> str:
    """HTTP failure text without embedding request URLs or secrets."""
    return f"{context} HTTP {exc.code}"
