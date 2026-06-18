"""SQLAlchemy declarative base. All ORM models inherit from ``Base``."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
