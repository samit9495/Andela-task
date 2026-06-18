"""Database initialization. Creates all tables from the registered metadata.

This is intentionally not a migration system; per the project scope we use
``create_all`` on startup. Import ORM models here as they are added so their
tables are registered on ``Base.metadata`` before ``create_all`` runs.
"""

import backend.app.models  # noqa: F401  (registers ORM models on Base.metadata)
from backend.app.db.base import Base
from backend.app.db.session import engine


def init_db() -> None:
    """Create all tables that are registered on the metadata."""
    Base.metadata.create_all(bind=engine)
