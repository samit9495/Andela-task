"""Loads operator-authored runbooks from Markdown files with YAML frontmatter."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Runbook:
    """An in-memory runbook parsed from a Markdown file."""

    slug: str
    title: str
    category: str | None
    keywords: list[str] = field(default_factory=list)
    content: str = ""


class RunbookLoader:
    """Reads ``*.md`` runbooks from a directory."""

    def __init__(self, source_dir: str | Path) -> None:
        self._source_dir = Path(source_dir)

    def load_all(self) -> list[Runbook]:
        if not self._source_dir.is_dir():
            return []
        runbooks: list[Runbook] = []
        for path in sorted(self._source_dir.glob("*.md")):
            meta, body = self._split_frontmatter(path.read_text(encoding="utf-8"))
            runbooks.append(
                Runbook(
                    slug=path.stem,
                    title=str(meta.get("title", path.stem)),
                    category=meta.get("category"),
                    keywords=[str(keyword) for keyword in meta.get("keywords", [])],
                    content=body,
                )
            )
        return runbooks

    @staticmethod
    def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
        if not text.startswith("---"):
            return {}, text.strip()
        _, frontmatter, body = text.split("---", 2)
        meta = yaml.safe_load(frontmatter) or {}
        return meta, body.strip()
