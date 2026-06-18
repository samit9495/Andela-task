"""Deterministic AI-evaluation report generator.

Runs the triage agents against the fixed fixtures with the offline
``MockAIClient`` and renders a Markdown scorecard. No live API calls.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from backend.app.rag.embedder import HashingEmbedder
from backend.app.rag.retriever import RunbookRetriever
from backend.app.rag.runbook_loader import RunbookLoader
from backend.app.triage.agents.classification_agent import ClassificationAgent
from backend.app.triage.agents.remediation_agent import RemediationAgent
from backend.app.triage.agents.root_cause_agent import RootCauseAgent
from backend.app.triage.mock_ai_client import MockAIClient
from backend.app.triage.prompt_log import NullPromptLog

FIXTURE_DIR = Path("tests/ai_eval/fixtures")
ARTIFACT_PATH = Path("artifacts/ai_evaluations.md")


def _load_fixtures() -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8")) for path in sorted(FIXTURE_DIR.glob("*.json"))
    ]


def evaluate() -> dict:
    """Score classification, root-cause, and remediation grounding on fixtures."""
    client = MockAIClient()
    classifier = ClassificationAgent(client, NullPromptLog())
    analyst = RootCauseAgent(client, NullPromptLog())
    remediator = RemediationAgent(client, NullPromptLog())

    runbooks = RunbookLoader("data/runbooks").load_all()
    retriever = RunbookRetriever(HashingEmbedder(), runbooks, top_k=3, min_similarity=0.0)

    rows = []
    for data in _load_fixtures():
        payload = data["input"]
        top_events = [tuple(event) for event in payload["top_events"]]
        summary = payload["incident_summary"]

        category = classifier.classify(incident_summary=summary, top_events=top_events).category
        classification_ok = category.value == data["expected_category"]

        analysis = analyst.analyze(
            incident_summary=summary, category=category, top_events=top_events
        )
        root_cause = analysis.root_cause.lower()
        root_cause_ok = any(kw.lower() in root_cause for kw in data["expected_root_cause_keywords"])

        retrieved = retriever.retrieve(summary)
        remediation = remediator.recommend(
            incident_summary=summary,
            root_cause=analysis.root_cause,
            retrieved=retrieved,
        )
        remediation_ok = bool(remediation.recommended_actions)

        rows.append(
            {
                "scenario": data["scenario"],
                "expected_category": data["expected_category"],
                "predicted_category": category.value,
                "classification_ok": classification_ok,
                "root_cause_ok": root_cause_ok,
                "remediation_ok": remediation_ok,
            }
        )

    total = len(rows)
    return {
        "rows": rows,
        "classification_accuracy": sum(r["classification_ok"] for r in rows) / total,
        "root_cause_accuracy": sum(r["root_cause_ok"] for r in rows) / total,
        "remediation_quality": sum(r["remediation_ok"] for r in rows) / total,
    }


def render_markdown(results: dict) -> str:
    lines = [
        "# AI Evaluation Report",
        "",
        f"_Generated: {datetime.now(UTC).isoformat()}_",
        "",
        "Deterministic offline evaluation (`MockAIClient`, `temperature=0.0`). "
        "No live Gemini calls.",
        "",
        "## Summary",
        "",
        "| Metric | Score |",
        "| --- | --- |",
        f"| Classification accuracy | {results['classification_accuracy']:.0%} |",
        f"| Root-cause accuracy | {results['root_cause_accuracy']:.0%} |",
        f"| Remediation quality | {results['remediation_quality']:.0%} |",
        "",
        "## Per-scenario",
        "",
        "| Scenario | Expected | Predicted | Classification | Root cause | Remediation |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    tick = {True: "PASS", False: "FAIL"}
    for row in results["rows"]:
        lines.append(
            f"| {row['scenario']} | {row['expected_category']} | "
            f"{row['predicted_category']} | {tick[row['classification_ok']]} | "
            f"{tick[row['root_cause_ok']]} | {tick[row['remediation_ok']]} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_report() -> Path:
    """Evaluate and persist the Markdown report; return its path."""
    results = evaluate()
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(render_markdown(results), encoding="utf-8")
    return ARTIFACT_PATH
