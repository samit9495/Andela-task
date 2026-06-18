"""Dashboard channel: the alert row itself is what the dashboard renders."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class DashboardAlertChannel:
    name = "dashboard"

    def send(self, payload: dict[str, Any]) -> None:
        logger.info("dashboard alert incident_id=%s", payload.get("incident_id"))
