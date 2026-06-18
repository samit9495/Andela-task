"""Unit tests for the topology seeder."""

import json

from backend.app.repositories.topology_repository import ServiceTopologyRepository
from backend.app.topology.seed import seed_topology


class TestSeedTopology:
    def test_seeds_from_json(self, db, tmp_path):
        path = tmp_path / "topology.json"
        path.write_text(json.dumps({"a": ["b"], "b": []}), encoding="utf-8")

        seed_topology(db, path)

        assert ServiceTopologyRepository(db).count() == 2

    def test_is_idempotent(self, db, tmp_path):
        path = tmp_path / "topology.json"
        path.write_text(json.dumps({"a": ["b"], "b": []}), encoding="utf-8")

        seed_topology(db, path)
        seed_topology(db, path)

        assert ServiceTopologyRepository(db).count() == 2

    def test_missing_file_is_noop(self, db, tmp_path):
        seed_topology(db, tmp_path / "missing.json")

        assert ServiceTopologyRepository(db).count() == 0
