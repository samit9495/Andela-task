"""Exceptions raised by the Watchdog SDK."""

from __future__ import annotations


class WatchdogError(Exception):
    """Base class for all SDK errors."""


class WatchdogAPIError(WatchdogError):
    """The API returned a 4xx/5xx response."""

    def __init__(self, status_code: int, code: str, detail: str) -> None:
        self.status_code = status_code
        self.code = code
        self.detail = detail
        super().__init__(f"[{status_code} {code}] {detail}")


class WatchdogTimeout(WatchdogError):
    """The request timed out or the connection failed after retries."""


class WatchdogValidationError(WatchdogError):
    """The API response did not match the expected schema."""
