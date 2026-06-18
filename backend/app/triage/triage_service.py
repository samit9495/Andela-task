"""Orchestrates the four-agent triage pipeline for an incident.

Classification -> Root Cause -> RAG retrieval -> Remediation -> Executive Summary.
Persists the AI fields onto the incident and returns an ``IncidentReport``. Agents
never raise (they fall back), so triage never crashes a request.
"""

from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.models.incident import Incident
from backend.app.rag.retriever import RunbookRetriever
from backend.app.triage.agents.classification_agent import ClassificationAgent
from backend.app.triage.agents.executive_summary_agent import ExecutiveSummaryAgent
from backend.app.triage.agents.remediation_agent import RemediationAgent
from backend.app.triage.agents.root_cause_agent import RootCauseAgent
from backend.app.triage.llm_client import LLMClient
from backend.app.triage.prompt_log import PromptLog
from backend.app.triage.schemas import IncidentReport


class TriageService:
    """Runs the agentic pipeline and records the result on the incident."""

    def __init__(
        self,
        db: Session,
        llm: LLMClient,
        retriever: RunbookRetriever,
        *,
        model: str,
        log_path: str | Path,
    ) -> None:
        self._db = db
        self._llm = llm
        self._retriever = retriever
        self._prompt_log = PromptLog(db, model=model, log_path=log_path)

    def triage(self, incident: Incident) -> IncidentReport:
        summary = self._incident_summary(incident)
        top_events = self._top_events(incident)
        log = self._prompt_log
        incident_id = incident.id

        classification = ClassificationAgent(self._llm, log, incident_id=incident_id).classify(
            incident_summary=summary, top_events=top_events
        )

        root_cause = RootCauseAgent(self._llm, log, incident_id=incident_id).analyze(
            incident_summary=summary,
            category=classification.category,
            top_events=top_events,
        )

        query = f"{classification.category.value} {root_cause.root_cause} " + " ".join(
            sig for sig, _, _ in top_events
        )
        retrieved = self._retriever.retrieve(query)

        remediation = RemediationAgent(self._llm, log, incident_id=incident_id).recommend(
            incident_summary=summary,
            root_cause=root_cause.root_cause,
            retrieved=retrieved,
        )

        exec_summary = ExecutiveSummaryAgent(self._llm, log, incident_id=incident_id).summarize(
            incident_summary=summary,
            category=classification.category,
            root_cause=root_cause.root_cause,
            recommended_actions=remediation.recommended_actions,
        )

        confidence = round((classification.confidence + root_cause.confidence) / 2, 2)
        incident.category = classification.category.value
        incident.root_cause = root_cause.root_cause
        incident.summary = exec_summary.executive_summary
        incident.confidence_score = confidence
        incident.recommended_actions = list(remediation.recommended_actions)
        incident.runbook_references = [ref.model_dump() for ref in remediation.references]
        self._db.commit()

        return IncidentReport(
            category=classification.category,
            confidence=confidence,
            root_cause=root_cause.root_cause,
            recommended_actions=remediation.recommended_actions,
            references=remediation.references,
            executive_summary=exec_summary.executive_summary,
        )

    @staticmethod
    def _incident_summary(incident: Incident) -> str:
        signatures = (
            ", ".join(a.signature for a in incident.anomalies if a.signature)
            or "no distinct signatures"
        )
        return (
            f"{incident.title} on service {incident.service or 'unknown'} "
            f"(severity {incident.severity}); {len(incident.anomalies)} anomalies "
            f"with signatures: {signatures}."
        )

    @staticmethod
    def _top_events(incident: Incident) -> list[tuple[str, int, str]]:
        return [
            (a.signature or a.strategy, int(a.current_value), "ERROR") for a in incident.anomalies
        ]
