"""Security tests for sensitive-value redaction."""

from red_govern.security.redaction import (
    redact_mapping,
    redact_text,
)


def test_sensitive_mapping_values_are_redacted() -> None:
    """Sensitive mapping keys should never expose values."""
    source = {
        "host": "example.redshift.amazonaws.com",
        "password": "secret-password",
        "nested": {
            "session_token": "token-value",
        },
    }

    result = redact_mapping(source)

    assert result["host"] == "example.redshift.amazonaws.com"
    assert result["password"] == "***REDACTED***"
    assert result["nested"]["session_token"] == "***REDACTED***"


def test_sensitive_text_is_redacted() -> None:
    """Credential-like text should be sanitised."""
    source = "password=secret-password connection failed"

    result = redact_text(source)

    assert "secret-password" not in result
    assert "***REDACTED***" in result
