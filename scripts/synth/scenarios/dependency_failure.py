"""Service dependency failure: a root service fails and cascades to dependents.

Reads the same ``data/topology.json`` the platform uses, then propagates the
failure down the dependency chain with realistic per-layer delays.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path
from random import Random

from .base import GeneratedEvent

_ROOT = "postgres"
_LAYER_DELAY_SECONDS = 10
_FAILURE_START = 5

_FALLBACK_TOPOLOGY: dict[str, list[str]] = {
    "checkout-service": ["payment-api", "auth-service"],
    "payment-api": ["postgres", "auth-service"],
    "orders-api": ["postgres", "payment-api"],
    "auth-service": ["postgres", "redis"],
    "notifications": ["redis"],
    "postgres": [],
    "redis": [],
}


def _default_topology_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "topology.json"


class DependencyFailureScenario:
    name = "dependency_failure"

    def __init__(self, topology_path: str | Path | None = None) -> None:
        self._topology_path = Path(topology_path) if topology_path else _default_topology_path()

    def generate(
        self, *, start: datetime, duration_seconds: int, rng: Random
    ) -> Iterator[GeneratedEvent]:
        adjacency = self._load_topology()
        dependents = _reverse(adjacency)
        root = _ROOT if _ROOT in adjacency else next(iter(sorted(adjacency)), _ROOT)
        layers = _failure_layers(root, dependents)
        services = sorted(adjacency)

        for second in range(duration_seconds):
            ts = start + timedelta(seconds=second)
            for service in services:
                if rng.random() < 0.2:
                    yield GeneratedEvent(service, "INFO", "request handled", ts)
            for depth, layer in enumerate(layers):
                if second < _FAILURE_START + depth * _LAYER_DELAY_SECONDS:
                    continue
                for service in layer:
                    if rng.random() < 0.5:
                        level = "CRITICAL" if depth == 0 and rng.random() < 0.3 else "ERROR"
                        message = f"Dependency failure: {service} unavailable (root cause: {root})"
                        yield GeneratedEvent(service, level, message, ts)

    def _load_topology(self) -> dict[str, list[str]]:
        try:
            return dict(json.loads(self._topology_path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            return dict(_FALLBACK_TOPOLOGY)


def _reverse(adjacency: dict[str, list[str]]) -> dict[str, list[str]]:
    dependents: dict[str, set[str]] = {service: set() for service in adjacency}
    for service, deps in adjacency.items():
        for dep in deps:
            dependents.setdefault(dep, set()).add(service)
    return {service: sorted(values) for service, values in dependents.items()}


def _failure_layers(root: str, dependents: dict[str, list[str]]) -> list[list[str]]:
    layers = [[root]]
    seen = {root}
    frontier = [root]
    while frontier:
        nxt: list[str] = []
        for node in frontier:
            for dependent in dependents.get(node, []):
                if dependent not in seen:
                    seen.add(dependent)
                    nxt.append(dependent)
        if nxt:
            layers.append(sorted(nxt))
        frontier = nxt
    return layers
