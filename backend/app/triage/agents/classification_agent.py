"""Classification Agent: assigns an incident category."""

from backend.app.models.enums import IncidentCategory
from backend.app.triage.base_agent import StructuredAgent, format_top_events
from backend.app.triage.prompts import CLASSIFICATION_PROMPT_V1
from backend.app.triage.sanitize import sanitize
from backend.app.triage.schemas import ClassificationOutput


class ClassificationAgent(StructuredAgent):
    NAME = "classification"
    PROMPT_VERSION = "classification_v1"

    def classify(
        self, *, incident_summary: str, top_events: list[tuple[str, int, str]]
    ) -> ClassificationOutput:
        prompt = CLASSIFICATION_PROMPT_V1.format(
            incident_summary=sanitize(incident_summary),
            top_events_block=format_top_events(top_events),
        )
        output = self._complete(
            prompt=prompt,
            schema=ClassificationOutput,
            prompt_version=self.PROMPT_VERSION,
            max_tokens=256,
        )
        if output is not None:
            return output
        return ClassificationOutput(
            category=IncidentCategory.UNKNOWN,
            confidence=0.0,
            reasoning="Triage unavailable; fell back to deterministic default.",
        )
