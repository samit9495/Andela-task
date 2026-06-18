"""Domain enumerations shared by ORM models and Pydantic schemas."""

from enum import Enum


class LogLevel(str, Enum):
    """Canonical, standardized log severity levels."""

    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Severity(str, Enum):
    """Incident severity levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class IncidentStatus(str, Enum):
    """Incident lifecycle states."""

    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    MITIGATED = "MITIGATED"
    RESOLVED = "RESOLVED"


class IncidentCategory(str, Enum):
    """AI-assigned incident category (Classification Agent)."""

    DATABASE = "database"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    UNKNOWN = "unknown"


class AlertChannel(str, Enum):
    """Alert delivery channels (all simulated in this project)."""

    DASHBOARD = "dashboard"
    WEBHOOK = "webhook"
    EMAIL = "email"
    SLACK = "slack"


class AlertStatus(str, Enum):
    """Lifecycle of a fired alert."""

    SENT = "SENT"
    SUPPRESSED = "SUPPRESSED"
