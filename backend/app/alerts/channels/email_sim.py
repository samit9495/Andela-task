"""Simulated email channel: logs a sanitized payload instead of sending mail."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EmailAlertChannel:
    name = "email"

    def send(self, payload: dict[str, Any]) -> None:
        logger.info("email alert incident_id=%s", payload.get("incident_id"))
