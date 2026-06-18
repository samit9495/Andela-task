"""Remediation Agent: recommends actions grounded in retrieved runbooks."""

from backend.app.rag.retriever import RetrievalResult
from backend.app.triage.base_agent import StructuredAgent
from backend.app.triage.prompts import REMEDIATION_PROMPT_V1
from backend.app.triage.sanitize import sanitize
from backend.app.triage.schemas import RemediationActions, RemediationOutput, RunbookReference

_RUNBOOK_EXCERPT_CHARS = 800
_FALLBACK_ACTIONS = [
    "Investigate the dominant error signature on the affected service.",
    "Roll back the most recent correlated deployment if applicable.",
    "Escalate to the on-call owner if the error rate keeps climbing.",
]


class RemediationAgent(StructuredAgent):
    NAME = "remediation"
    PROMPT_VERSION = "remediation_v1"

    def recommend(
        self,
        *,
        incident_summary: str,
        root_cause: str,
        retrieved: list[RetrievalResult],
    ) -> RemediationOutput:
        prompt = REMEDIATION_PROMPT_V1.format(
            incident_summary=sanitize(incident_summary),
            root_cause=sanitize(root_cause),
            runbook_block=self._runbook_block(retrieved),
        )
        output = self._complete(
            prompt=prompt,
            schema=RemediationActions,
            prompt_version=self.PROMPT_VERSION,
            max_tokens=512,
        )
        actions = output.recommended_actions if output is not None else list(_FALLBACK_ACTIONS)
        references = [RunbookReference(slug=r.slug, title=r.title) for r in retrieved]
        return RemediationOutput(recommended_actions=actions, references=references)

    @staticmethod
    def _runbook_block(retrieved: list[RetrievalResult]) -> str:
        if not retrieved:
            return "- (no runbooks matched)"
        return "\n\n".join(
            f"### Runbook: {r.title}\n{r.content[:_RUNBOOK_EXCERPT_CHARS]}" for r in retrieved
        )
