"""Sensitive-value redaction utilities."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = {
    "password",
    "secret",
    "secret_access_key",
    "secret_access_key_id",
    "access_key",
    "access_key_id",
    "session_token",
    "token",
    "web_identity_token",
}

SENSITIVE_TEXT_PATTERNS = (
    re.compile(
        r"(?i)(password|secret|token|access[_ -]?key)"
        r"\s*[=:]\s*[^\s,;]+"
    ),
)


def is_sensitive_key(key: str) -> bool:
    """Return whether a key represents sensitive information."""
    normalised = key.lower().strip()

    return any(
        sensitive in normalised
        for sensitive in SENSITIVE_KEYS
    )


def redact_mapping(
    values: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a recursively redacted mapping."""
    redacted: dict[str, Any] = {}

    for key, value in values.items():
        if is_sensitive_key(key):
            redacted[key] = "***REDACTED***"
        elif isinstance(value, Mapping):
            redacted[key] = redact_mapping(value)
        elif isinstance(value, list):
            redacted[key] = [
                redact_mapping(item)
                if isinstance(item, Mapping)
                else item
                for item in value
            ]
        else:
            redacted[key] = value

    return redacted


def redact_text(value: str) -> str:
    """Redact likely credentials from text."""
    redacted = value

    for pattern in SENSITIVE_TEXT_PATTERNS:
        redacted = pattern.sub(
            lambda match: f"{match.group(1)}=***REDACTED***",
            redacted,
        )

    return redacted
