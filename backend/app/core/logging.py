"""Logging configuration. Kept minimal and PII-safe by default."""

import logging

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging at the given level (defaults to INFO)."""
    resolved = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=resolved, format=_LOG_FORMAT)
