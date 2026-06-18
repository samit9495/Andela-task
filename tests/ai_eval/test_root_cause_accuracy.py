"""AI evaluation: root-cause accuracy on fixed scenarios (deterministic, no live API)."""

import json
from pathlib import Path

import pytest
from backend.app.triage.agents.classification_agent import ClassificationAgent
from backend.app.triage.agents.root_cause_agent import RootCauseAgent
from backend.app.triage.mock_ai_client import MockAIClient
from backend.app.triage.prompt_log import NullPromptLog

_FIXTURE_DIR = Path("tests/ai_eval/fixtures")
_ACCURACY_THRESHOLD = 0.8


@pytest.mark.ai_eval
class TestRootCauseAccuracy:
    def test_accuracy_meets_threshold(self):
        client = MockAIClient()
        classifier = ClassificationAgent(client, NullPromptLog())
        analyst = RootCauseAgent(client, NullPromptLog())
        fixtures = sorted(_FIXTURE_DIR.glob("*.json"))
        assert len(fixtures) >= 5

        correct = 0
        for path in fixtures:
            data = json.loads(path.read_text(encoding="utf-8"))
            payload = data["input"]
            top_events = [tuple(event) for event in payload["top_events"]]
            category = classifier.classify(
                incident_summary=payload["incident_summary"], top_events=top_events
            ).category
            analysis = analyst.analyze(
                incident_summary=payload["incident_summary"],
                category=category,
                top_events=top_events,
            )
            root_cause = analysis.root_cause.lower()
            keywords = data["expected_root_cause_keywords"]
            correct += int(any(keyword.lower() in root_cause for keyword in keywords))

        assert correct / len(fixtures) >= _ACCURACY_THRESHOLD
