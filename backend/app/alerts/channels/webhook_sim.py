"""Simulated webhook channel: logs a sanitized payload instead of an HTTP call."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class WebhookAlertChannel:
    name = "webhook"

    def send(self, payload: dict[str, Any]) -> None:
        logger.info(
            "webhook alert incident_id=%s severity=%s",
            payload.get("incident_id"),
            payload.get("severity"),
        )
