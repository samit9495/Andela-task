"""Executive Summary Agent: a leadership-facing narrative."""

from backend.app.models.enums import IncidentCategory
from backend.app.triage.base_agent import StructuredAgent
from backend.app.triage.prompts import EXECUTIVE_SUMMARY_PROMPT_V1
from backend.app.triage.sanitize import sanitize
from backend.app.triage.schemas import ExecutiveSummaryOutput


class ExecutiveSummaryAgent(StructuredAgent):
    NAME = "executive_summary"
    PROMPT_VERSION = "executive_summary_v1"

    def summarize(
        self,
        *,
        incident_summary: str,
        category: IncidentCategory,
        root_cause: str,
        recommended_actions: list[str],
    ) -> ExecutiveSummaryOutput:
        prompt = EXECUTIVE_SUMMARY_PROMPT_V1.format(
            category=category.value,
            incident_summary=sanitize(incident_summary),
            root_cause=sanitize(root_cause),
            actions_block="\n".join(f"- {action}" for action in recommended_actions) or "- (none)",
        )
        output = self._complete(
            prompt=prompt,
            schema=ExecutiveSummaryOutput,
            prompt_version=self.PROMPT_VERSION,
            max_tokens=512,
        )
        if output is not None:
            return output
        return ExecutiveSummaryOutput(
            executive_summary=(
                f"A {category.value} incident was detected. Probable cause: {root_cause}. "
                "Automated summary (triage fallback); review the recommended actions."
            )
        )
