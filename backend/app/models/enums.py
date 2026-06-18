"""Domain enumerations shared by ORM models and Pydantic schemas."""

from enum import Enum


class LogLevel(str, Enum):
    """Canonical, standardized log severity levels."""

    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
