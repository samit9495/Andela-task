"""Tests for the synthetic traffic scenarios. All deterministic via seeded RNG."""

from datetime import UTC, datetime
from random import Random

import pytest
from scripts.synth.registry import SCENARIOS, get_scenario
from scripts.synth.scenarios.auth_failures import AuthFailuresScenario
from scripts.synth.scenarios.black_friday import BlackFridayScenario
from scripts.synth.scenarios.database_outage import DatabaseOutageScenario
from scripts.synth.scenarios.dependency_failure import DependencyFailureScenario
from scripts.synth.scenarios.memory_leak import MemoryLeakScenario
from scripts.synth.scenarios.normal import NormalScenario
from scripts.synth.scenarios.throttling import ThrottlingScenario

_START = datetime(2026, 6, 18, 10, 0, 0, tzinfo=UTC)
_VALID_LEVELS = {"INFO", "WARN", "ERROR", "CRITICAL"}


def _run(scenario, *, duration=60, seed=42):
    return list(scenario.generate(start=_START, duration_seconds=duration, rng=Random(seed)))


@pytest.mark.parametrize(
    "scenario",
    [
        NormalScenario(),
        DatabaseOutageScenario(),
        AuthFailuresScenario(),
        ThrottlingScenario(),
        MemoryLeakScenario(),
        DependencyFailureScenario(),
        BlackFridayScenario(),
    ],
)
class TestEveryScenario:
    def test_produces_events_within_window_and_valid_levels(self, scenario):
        events = _run(scenario)

        assert len(events) > 0
        assert all(event.level in _VALID_LEVELS for event in events)
        assert all(event.timestamp >= _START for event in events)

    def test_is_deterministic_with_same_seed(self, scenario):
        assert _run(scenario, seed=7) == _run(scenario, seed=7)


class TestScenarioCharacter:
    def test_normal_is_majority_info(self):
        events = _run(NormalScenario())
        info = sum(1 for e in events if e.level == "INFO")
        assert info / len(events) >= 0.85

    def test_database_outage_clusters_db_errors(self):
        events = _run(DatabaseOutageScenario())
        db_errors = [
            e for e in events if e.level in {"ERROR", "CRITICAL"} and "atabase" in e.message
        ]
        assert len(db_errors) >= 10

    def test_auth_failures_target_auth_service(self):
        events = _run(AuthFailuresScenario())
        auth_errors = [e for e in events if e.level == "ERROR" and e.service == "auth-service"]
        assert len(auth_errors) >= 10
        assert any("401" in e.message or "JWT" in e.message for e in auth_errors)

    def test_throttling_emits_429_on_gateway(self):
        events = _run(ThrottlingScenario())
        throttled = [e for e in events if "429" in e.message]
        assert len(throttled) >= 10
        assert all(e.service == "api-gateway" for e in throttled)

    def test_memory_leak_errors_rise_over_time(self):
        events = _run(MemoryLeakScenario(), duration=120)
        errors = [e for e in events if e.level in {"ERROR", "CRITICAL"}]
        midpoint = _START.timestamp() + 60
        early = sum(1 for e in errors if e.timestamp.timestamp() < midpoint)
        late = sum(1 for e in errors if e.timestamp.timestamp() >= midpoint)
        assert late > early

    def test_dependency_failure_cascades_to_dependents(self):
        events = _run(DependencyFailureScenario())
        services = {e.service for e in events if e.level in {"ERROR", "CRITICAL"}}
        # postgres is the root; payment-api and auth-service depend on it.
        assert "postgres" in services
        assert "payment-api" in services

    def test_dependency_failure_uses_fallback_when_topology_missing(self):
        scenario = DependencyFailureScenario(topology_path="/nonexistent/topology.json")

        events = _run(scenario)
        services = {e.service for e in events if e.level in {"ERROR", "CRITICAL"}}

        assert "postgres" in services
        assert "payment-api" in services

    def test_black_friday_high_volume_mostly_info_with_errors(self):
        normal = _run(NormalScenario())
        black_friday = _run(BlackFridayScenario())
        assert len(black_friday) > len(normal)
        info = sum(1 for e in black_friday if e.level == "INFO")
        errors = sum(1 for e in black_friday if e.level in {"ERROR", "CRITICAL"})
        assert info > errors
        assert errors >= 10


class TestRegistry:
    def test_registry_has_all_seven_scenarios(self):
        assert set(SCENARIOS) == {
            "normal",
            "db_outage",
            "auth_failures",
            "throttling",
            "memory_leak",
            "dependency_failure",
            "black_friday",
        }

    def test_get_scenario_returns_instance(self):
        assert isinstance(get_scenario("normal"), NormalScenario)

    def test_get_scenario_unknown_raises(self):
        with pytest.raises(KeyError):
            get_scenario("nope")
