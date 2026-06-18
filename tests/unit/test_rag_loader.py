"""Unit tests for the runbook loader."""

from backend.app.rag.runbook_loader import RunbookLoader

_DOC = """---
title: Database Timeout
category: database
keywords: [timeout, pool]
version: 2
---
# Body
Some content.
"""


class TestRunbookLoader:
    def test_loads_runbook_with_frontmatter(self, tmp_path):
        (tmp_path / "database_timeout.md").write_text(_DOC, encoding="utf-8")

        runbooks = RunbookLoader(tmp_path).load_all()

        assert len(runbooks) == 1
        runbook = runbooks[0]
        assert runbook.slug == "database_timeout"
        assert runbook.title == "Database Timeout"
        assert runbook.category == "database"
        assert runbook.keywords == ["timeout", "pool"]
        assert "Some content." in runbook.content

    def test_ignores_non_markdown_and_sorts(self, tmp_path):
        (tmp_path / "b.md").write_text("---\ntitle: B\n---\nB", encoding="utf-8")
        (tmp_path / "a.md").write_text("---\ntitle: A\n---\nA", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("ignore me", encoding="utf-8")

        runbooks = RunbookLoader(tmp_path).load_all()

        assert [rb.slug for rb in runbooks] == ["a", "b"]

    def test_empty_dir_returns_empty(self, tmp_path):
        assert RunbookLoader(tmp_path).load_all() == []

    def test_missing_dir_returns_empty(self, tmp_path):
        assert RunbookLoader(tmp_path / "does_not_exist").load_all() == []

    def test_file_without_frontmatter_loads_body(self, tmp_path):
        (tmp_path / "plain.md").write_text("# Just a body\nno frontmatter", encoding="utf-8")

        runbooks = RunbookLoader(tmp_path).load_all()

        assert runbooks[0].title == "plain"
        assert runbooks[0].keywords == []
        assert "Just a body" in runbooks[0].content
