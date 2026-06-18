"""Loads the service topology graph from a JSON file into the database."""

import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.repositories.topology_repository import ServiceTopologyRepository

logger = logging.getLogger(__name__)


def seed_topology(db: Session, path: str | Path) -> None:
    """Idempotently upsert the topology defined in ``path``. No-op if absent."""
    source = Path(path)
    if not source.exists():
        logger.warning("topology seed file not found at %s; skipping", source)
        return
    graph: dict[str, list[str]] = json.loads(source.read_text(encoding="utf-8"))
    repo = ServiceTopologyRepository(db)
    for service, depends_on in graph.items():
        repo.upsert(service, list(depends_on))
    db.commit()
