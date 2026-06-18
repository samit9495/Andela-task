"""Event normalization: stable signatures and standardized severity levels.

A *signature* is a message template with dynamic values (numbers, UUIDs,
timestamps, IP addresses, hex) replaced by placeholders, so messages that differ
only in their dynamic parts collapse to the same signature.
"""

import re

from backend.app.core.exceptions import EventValidationError
from backend.app.models.enums import LogLevel

_UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_TIMESTAMP_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"
)
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_TIME_RE = re.compile(r"\b\d{2}:\d{2}:\d{2}(?:\.\d+)?\b")
_IP_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
_HEX_RE = re.compile(r"\b0[xX][0-9a-fA-F]+\b")
_NUM_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
_WHITESPACE_RE = re.compile(r"\s+")

# Ordered: timestamp/date/time before UUID; IP and hex before plain numbers.
_SUBSTITUTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (_TIMESTAMP_RE, "<TIMESTAMP>"),
    (_DATE_RE, "<TIMESTAMP>"),
    (_TIME_RE, "<TIMESTAMP>"),
    (_UUID_RE, "<UUID>"),
    (_IP_RE, "<IP>"),
    (_HEX_RE, "<HEX>"),
    (_NUM_RE, "<NUM>"),
)

_LEVEL_MAP: dict[str, LogLevel] = {
    "INFO": LogLevel.INFO,
    "INFORMATION": LogLevel.INFO,
    "NOTICE": LogLevel.INFO,
    "DEBUG": LogLevel.INFO,
    "TRACE": LogLevel.INFO,
    "WARN": LogLevel.WARN,
    "WARNING": LogLevel.WARN,
    "ERROR": LogLevel.ERROR,
    "ERR": LogLevel.ERROR,
    "CRITICAL": LogLevel.CRITICAL,
    "CRIT": LogLevel.CRITICAL,
    "FATAL": LogLevel.CRITICAL,
    "EMERGENCY": LogLevel.CRITICAL,
    "ALERT": LogLevel.CRITICAL,
}


def generate_signature(message: str) -> str:
    """Return a stable signature for a raw log message."""
    signature = message
    for pattern, placeholder in _SUBSTITUTIONS:
        signature = pattern.sub(placeholder, signature)
    return _WHITESPACE_RE.sub(" ", signature).strip()


def normalize_level(raw: str) -> LogLevel:
    """Standardize a raw severity string to a canonical ``LogLevel``."""
    key = raw.strip().upper()
    try:
        return _LEVEL_MAP[key]
    except KeyError as exc:
        raise EventValidationError(f"unsupported log level: {raw}") from exc
