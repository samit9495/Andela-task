"""AI evaluation: generate and validate the scorecard artifact (deterministic)."""

import pytest

from tests.ai_eval.report import ARTIFACT_PATH, evaluate, render_markdown, write_report

_THRESHOLD = 0.8


@pytest.mark.ai_eval
class TestEvaluationReport:
    def test_all_metrics_meet_threshold(self):
        results = evaluate()

        assert results["classification_accuracy"] >= _THRESHOLD
        assert results["root_cause_accuracy"] >= _THRESHOLD
        assert results["remediation_quality"] >= _THRESHOLD

    def test_report_renders_summary_and_rows(self):
        results = evaluate()

        markdown = render_markdown(results)

        assert "# AI Evaluation Report" in markdown
        assert "Classification accuracy" in markdown
        for row in results["rows"]:
            assert row["scenario"] in markdown

    def test_write_report_persists_artifact(self):
        path = write_report()

        assert path == ARTIFACT_PATH
        assert ARTIFACT_PATH.exists()
        assert "AI Evaluation Report" in ARTIFACT_PATH.read_text(encoding="utf-8")
