"""Unit tests for the ServiceTopologyRepository."""

from backend.app.repositories.topology_repository import ServiceTopologyRepository


class TestServiceTopologyRepository:
    def test_upsert_and_adjacency(self, db):
        repo = ServiceTopologyRepository(db)
        repo.upsert("a", ["b"])
        repo.upsert("b", [])
        db.commit()

        assert repo.adjacency() == {"a": ["b"], "b": []}

    def test_upsert_updates_existing_without_duplicating(self, db):
        repo = ServiceTopologyRepository(db)
        repo.upsert("a", ["b"])
        db.commit()
        repo.upsert("a", ["c"])
        db.commit()

        assert repo.adjacency()["a"] == ["c"]
        assert repo.count() == 1
