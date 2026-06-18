"""watchdog_client — a typed Python SDK for the Agentic Observability Platform."""

from .client import WatchdogClient
from .exceptions import (
    WatchdogAPIError,
    WatchdogError,
    WatchdogTimeout,
    WatchdogValidationError,
)
from .models import (
    AlertRead,
    AnomalyRead,
    BatchEventResult,
    EventCreate,
    EventRead,
    HealthStatus,
    IncidentRead,
    RiskScore,
    RunbookReference,
)

__version__ = "0.2.0"

__all__ = [
    "WatchdogClient",
    "EventCreate",
    "EventRead",
    "BatchEventResult",
    "IncidentRead",
    "AnomalyRead",
    "RunbookReference",
    "AlertRead",
    "RiskScore",
    "HealthStatus",
    "WatchdogError",
    "WatchdogAPIError",
    "WatchdogTimeout",
    "WatchdogValidationError",
    "__version__",
]
