"""Shared pytest fixtures.

Tests run against an in-memory SQLite database. The application's own engine is
also pointed at in-memory storage (via ``WATCHDOG_DATABASE_URL``) so startup
never writes a file during the test run.
"""

import os

os.environ["WATCHDOG_DATABASE_URL"] = "sqlite://"

from collections.abc import Iterator  # noqa: E402

import backend.app.models  # noqa: E402, F401  (registers ORM models on Base.metadata)
import pytest  # noqa: E402
from backend.app.db.base import Base  # noqa: E402
from backend.app.db.session import get_db  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.triage.llm_client import FakeLLMClient  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402


@pytest.fixture
def engine() -> Iterator[Engine]:
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def fake_llm() -> FakeLLMClient:
    """Deterministic LLM test double; register canned outputs per schema."""
    return FakeLLMClient()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
