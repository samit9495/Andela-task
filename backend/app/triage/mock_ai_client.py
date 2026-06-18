"""Offline heuristic LLM client.

Used when ``USE_MOCK_AI=true`` or no Gemini key is configured. It produces
deterministic, plausible structured outputs from keyword heuristics so the full
triage pipeline (and the demo) works without any network access.
"""

import re

from backend.app.core.exceptions import LLMResponseInvalid
from backend.app.models.enums import IncidentCategory
from backend.app.triage.llm_client import T

_INPUT_RE = re.compile(r"<<<INPUT>>>(.*?)<<<END>>>", re.DOTALL)
_EXPLICIT_CATEGORY_RE = re.compile(r"^Category:\s*([a-zA-Z_]+)\s*$", re.MULTILINE)

_CATEGORY_KEYWORDS: dict[IncidentCategory, tuple[str, ...]] = {
    IncidentCategory.DATABASE: ("database", "db", "sql", "pool", "query", "deadlock", "timeout"),
    IncidentCategory.AUTHENTICATION: ("auth", "login", "jwt", "token", "credential", "401", "403"),
    IncidentCategory.NETWORK: ("network", "dns", "connection refused", "unreachable", "socket"),
    IncidentCategory.INFRASTRUCTURE: ("cpu", "memory", "oom", "disk", "host", "node", "kubernetes"),
}

_ACTIONS: dict[IncidentCategory, tuple[str, ...]] = {
    IncidentCategory.DATABASE: (
        "Inspect connection pool saturation and increase pool size if exhausted.",
        "Identify and terminate long-running or blocking queries.",
    ),
    IncidentCategory.AUTHENTICATION: (
        "Verify identity provider availability and token signing keys.",
        "Check for expired credentials or clock skew on auth services.",
    ),
    IncidentCategory.NETWORK: (
        "Check DNS resolution and upstream service reachability.",
        "Review recent network or firewall configuration changes.",
    ),
    IncidentCategory.INFRASTRUCTURE: (
        "Inspect host CPU/memory/disk utilization and scale or restart as needed.",
        "Review recent deployments for resource regressions.",
    ),
    IncidentCategory.APPLICATION: (
        "Review recent application deployments and roll back if correlated.",
        "Inspect error logs for the dominant failure signature.",
    ),
}


class MockAIClient:
    """Heuristic, deterministic ``LLMClient`` for offline operation."""

    def complete_structured(
        self,
        *,
        prompt: str,
        schema: type[T],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        request_id: str,
    ) -> T:
        category = self._classify(prompt)
        builders = {
            "ClassificationOutput": lambda: schema(
                category=category,
                confidence=0.6,
                reasoning="Heuristic keyword classification (mock AI).",
            ),
            "RootCauseAnalysis": lambda: schema(
                root_cause=(
                    f"Probable {category.value} subsystem degradation inferred from "
                    "the dominant event signatures."
                ),
                confidence=0.5,
            ),
            "RemediationActions": lambda: schema(
                recommended_actions=list(_ACTIONS[category]),
            ),
            "ExecutiveSummaryOutput": lambda: schema(
                executive_summary=(
                    f"A {category.value} incident was detected and triaged automatically "
                    "(mock AI). Review the root cause and remediation steps below."
                ),
            ),
        }
        builder = builders.get(schema.__name__)
        if builder is None:
            raise LLMResponseInvalid(f"MockAIClient cannot synthesize {schema.__name__}")
        return builder()

    @staticmethod
    def _classify(prompt: str) -> IncidentCategory:
        match = _INPUT_RE.search(prompt)
        block = match.group(1) if match else prompt
        # Prompts that explicitly carry a `Category: <name>` hint (e.g. the
        # executive-summary prompt) should honor it so downstream agents stay
        # consistent with the upstream classifier; otherwise fall back to the
        # keyword heuristic.
        explicit = _EXPLICIT_CATEGORY_RE.search(block)
        if explicit is not None:
            try:
                return IncidentCategory(explicit.group(1).lower())
            except ValueError:
                pass
        text = block.lower()
        for category, keywords in _CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return category
        return IncidentCategory.APPLICATION
