"""Service dependency graph: blast radius and root-cause locality.

``adjacency`` maps a service to the services it depends on. The blast radius of
a failing service is everything that (transitively) depends on it.
"""

from collections.abc import Iterable, Mapping


class TopologyEngine:
    """Pure graph queries over a service dependency map."""

    def __init__(self, adjacency: Mapping[str, list[str]]) -> None:
        self._adjacency: dict[str, list[str]] = {k: list(v) for k, v in adjacency.items()}
        self._nodes: set[str] = set(self._adjacency)
        for deps in self._adjacency.values():
            self._nodes.update(deps)
        self._dependents: dict[str, set[str]] = {node: set() for node in self._nodes}
        for service, deps in self._adjacency.items():
            for dep in deps:
                self._dependents[dep].add(service)

    def services(self) -> list[str]:
        return sorted(self._nodes)

    def depends_on(self, service: str) -> list[str]:
        return list(self._adjacency.get(service, []))

    def edges(self) -> list[tuple[str, str]]:
        return sorted((service, dep) for service, deps in self._adjacency.items() for dep in deps)

    def blast_radius(self, service: str) -> set[str]:
        if service not in self._nodes:
            return set()
        impacted: set[str] = set()
        queue = [service]
        while queue:
            current = queue.pop()
            for dependent in self._dependents.get(current, set()):
                if dependent not in impacted:
                    impacted.add(dependent)
                    queue.append(dependent)
        return impacted

    def root_service(self, services: Iterable[str]) -> str | None:
        candidates = [service for service in sorted(set(services)) if service in self._nodes]
        if not candidates:
            return None
        return max(candidates, key=lambda service: len(self.blast_radius(service)))
