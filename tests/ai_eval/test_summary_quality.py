"""AI evaluation: executive-summary quality rubric (deterministic, no live API)."""

import json
from pathlib import Path

import pytest
from backend.app.triage.agents.classification_agent import ClassificationAgent
from backend.app.triage.agents.executive_summary_agent import ExecutiveSummaryAgent
from backend.app.triage.agents.remediation_agent import RemediationAgent
from backend.app.triage.agents.root_cause_agent import RootCauseAgent
from backend.app.triage.mock_ai_client import MockAIClient
from backend.app.triage.prompt_log import NullPromptLog

_FIXTURE_DIR = Path("tests/ai_eval/fixtures")
_QUALITY_THRESHOLD = 0.8


@pytest.mark.ai_eval
class TestSummaryQuality:
    def test_summary_contains_expected_keyword(self):
        client = MockAIClient()
        classifier = ClassificationAgent(client, NullPromptLog())
        analyst = RootCauseAgent(client, NullPromptLog())
        remediator = RemediationAgent(client, NullPromptLog())
        summarizer = ExecutiveSummaryAgent(client, NullPromptLog())
        fixtures = sorted(_FIXTURE_DIR.glob("*.json"))
        assert len(fixtures) >= 5

        correct = 0
        for path in fixtures:
            data = json.loads(path.read_text(encoding="utf-8"))
            payload = data["input"]
            top_events = [tuple(event) for event in payload["top_events"]]
            summary = payload["incident_summary"]

            category = classifier.classify(incident_summary=summary, top_events=top_events).category
            analysis = analyst.analyze(
                incident_summary=summary, category=category, top_events=top_events
            )
            remediation = remediator.recommend(
                incident_summary=summary,
                root_cause=analysis.root_cause,
                retrieved=[],
            )
            executive = summarizer.summarize(
                incident_summary=summary,
                category=category,
                root_cause=analysis.root_cause,
                recommended_actions=remediation.recommended_actions,
            )

            text = executive.executive_summary.lower()
            keywords = data["expected_summary_keywords"]
            correct += int(any(keyword.lower() in text for keyword in keywords))

        assert correct / len(fixtures) >= _QUALITY_THRESHOLD
