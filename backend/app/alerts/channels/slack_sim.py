"""Simulated Slack channel: logs a sanitized payload instead of calling Slack."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SlackAlertChannel:
    name = "slack"

    def send(self, payload: dict[str, Any]) -> None:
        logger.info("slack alert incident_id=%s", payload.get("incident_id"))
