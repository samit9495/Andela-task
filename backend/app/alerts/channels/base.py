"""The alert channel contract. All channels are simulated in this project."""

from typing import Any, Protocol


class AlertChannel(Protocol):
    """A delivery channel for an alert payload."""

    name: str

    def send(self, payload: dict[str, Any]) -> None:
        """Deliver (simulate delivery of) the alert payload."""
        ...
