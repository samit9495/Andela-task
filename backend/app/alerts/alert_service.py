"""Raises alerts for incidents across channels, with dedup and rate limiting."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from backend.app.alerts.channels.base import AlertChannel
from backend.app.alerts.channels.dashboard import DashboardAlertChannel
from backend.app.alerts.channels.email_sim import EmailAlertChannel
from backend.app.alerts.channels.slack_sim import SlackAlertChannel
from backend.app.alerts.channels.webhook_sim import WebhookAlertChannel
from backend.app.core.config import get_settings
from backend.app.models.alert import Alert
from backend.app.models.enums import AlertStatus
from backend.app.models.incident import Incident
from backend.app.repositories.alert_repository import AlertRepository


def default_channels() -> list[AlertChannel]:
    return [
        DashboardAlertChannel(),
        WebhookAlertChannel(),
        EmailAlertChannel(),
        SlackAlertChannel(),
    ]


class AlertService:
    """Fans an incident out to alert channels with dedup + rate limiting."""

    def __init__(
        self,
        db: Session,
        channels: list[AlertChannel] | None = None,
        rate_limit_seconds: int | None = None,
    ) -> None:
        self._db = db
        self._repo = AlertRepository(db)
        self._channels = channels if channels is not None else default_channels()
        self._rate_limit_seconds = (
            rate_limit_seconds
            if rate_limit_seconds is not None
            else get_settings().alert_rate_limit_seconds
        )

    def raise_for_incident(self, incident: Incident, now: datetime) -> list[Alert]:
        window_start = now - timedelta(seconds=self._rate_limit_seconds)
        payload = self._build_payload(incident)
        fired: list[Alert] = []
        for channel in self._channels:
            dedup_key = f"{incident.id}:{channel.name}"
            if self._repo.exists_since(dedup_key, window_start):
                continue
            channel.send(payload)
            alert = Alert(
                incident_id=incident.id,
                channel=channel.name,
                status=AlertStatus.SENT.value,
                dedup_key=dedup_key,
                payload=payload,
                created_at=now,
            )
            self._repo.add(alert)
            fired.append(alert)
        if fired:
            self._db.commit()
            for alert in fired:
                self._db.refresh(alert)
        return fired

    @staticmethod
    def _build_payload(incident: Incident) -> dict[str, Any]:
        """Sanitized alert payload — incident metadata only, never raw log messages."""
        return {
            "incident_id": incident.id,
            "title": incident.title,
            "service": incident.service,
            "severity": incident.severity,
            "category": incident.category,
            "status": incident.status,
            "summary": incident.summary,
        }
