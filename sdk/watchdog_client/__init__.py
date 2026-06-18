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
    IncidentRead,
    RiskScore,
    RunbookReference,
)

__version__ = "0.1.0"

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
    "WatchdogError",
    "WatchdogAPIError",
    "WatchdogTimeout",
    "WatchdogValidationError",
    "__version__",
]
