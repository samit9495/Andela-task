"""Database initialization. Creates all tables from the registered metadata.

This is intentionally not a migration system; per the project scope we use
``create_all`` on startup. Import ORM models here as they are added so their
tables are registered on ``Base.metadata`` before ``create_all`` runs.
"""

import backend.app.models  # noqa: F401  (registers ORM models on Base.metadata)
from backend.app.core.config import get_settings
from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.topology.seed import seed_topology


def init_db() -> None:
    """Create all tables and seed the service topology graph."""
    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    with SessionLocal() as session:
        seed_topology(session, settings.topology_path)
