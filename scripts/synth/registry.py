"""Registry mapping scenario names to their implementations."""

from __future__ import annotations

from .scenarios.auth_failures import AuthFailuresScenario
from .scenarios.base import Scenario
from .scenarios.black_friday import BlackFridayScenario
from .scenarios.database_outage import DatabaseOutageScenario
from .scenarios.dependency_failure import DependencyFailureScenario
from .scenarios.memory_leak import MemoryLeakScenario
from .scenarios.normal import NormalScenario
from .scenarios.throttling import ThrottlingScenario

SCENARIOS: dict[str, type[Scenario]] = {
    "normal": NormalScenario,
    "db_outage": DatabaseOutageScenario,
    "auth_failures": AuthFailuresScenario,
    "throttling": ThrottlingScenario,
    "memory_leak": MemoryLeakScenario,
    "dependency_failure": DependencyFailureScenario,
    "black_friday": BlackFridayScenario,
}


def get_scenario(name: str) -> Scenario:
    """Return a new scenario instance by name. Raises KeyError if unknown."""
    return SCENARIOS[name]()
