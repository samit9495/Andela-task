"""ORM models. Importing this package registers all tables on ``Base.metadata``."""

from backend.app.models.event import Event

__all__ = ["Event"]
