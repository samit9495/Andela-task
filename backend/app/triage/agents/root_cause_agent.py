"""Root Cause Agent: identifies the most probable cause."""

from backend.app.models.enums import IncidentCategory
from backend.app.triage.base_agent import StructuredAgent, format_top_events
from backend.app.triage.prompts import ROOT_CAUSE_PROMPT_V1
from backend.app.triage.sanitize import sanitize
from backend.app.triage.schemas import RootCauseAnalysis


class RootCauseAgent(StructuredAgent):
    NAME = "root_cause"
    PROMPT_VERSION = "root_cause_v1"

    def analyze(
        self,
        *,
        incident_summary: str,
        category: IncidentCategory,
        top_events: list[tuple[str, int, str]],
    ) -> RootCauseAnalysis:
        prompt = ROOT_CAUSE_PROMPT_V1.format(
            category=category.value,
            incident_summary=sanitize(incident_summary),
            top_events_block=format_top_events(top_events),
        )
        output = self._complete(
            prompt=prompt,
            schema=RootCauseAnalysis,
            prompt_version=self.PROMPT_VERSION,
            max_tokens=512,
        )
        if output is not None:
            return output
        return RootCauseAnalysis(
            root_cause="Root cause undetermined; triage unavailable.",
            confidence=0.0,
        )
