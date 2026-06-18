"""Unit tests for the database session helpers."""

from backend.app.db.session import _create_engine, get_db
from sqlalchemy.engine import Engine


class TestCreateEngine:
    def test_in_memory_url_returns_engine(self):
        assert isinstance(_create_engine("sqlite://"), Engine)

    def test_file_sqlite_url_returns_engine(self):
        assert isinstance(_create_engine("sqlite:///./var/example.db"), Engine)

    def test_non_sqlite_url_passes_empty_connect_args(self, monkeypatch):
        captured: dict[str, object] = {}

        def fake_create_engine(url, **kwargs):
            captured["url"] = url
            captured["kwargs"] = kwargs
            return "engine-sentinel"

        monkeypatch.setattr("backend.app.db.session.create_engine", fake_create_engine)

        result = _create_engine("postgresql+psycopg2://u:p@localhost/db")

        assert result == "engine-sentinel"
        assert captured["kwargs"]["connect_args"] == {}


class TestGetDb:
    def test_yields_a_session_and_closes_it(self):
        generator = get_db()
        session = next(generator)

        assert session is not None

        generator.close()
