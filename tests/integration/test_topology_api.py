"""Integration tests for the topology API."""

from backend.app.models.incident import Incident
from backend.app.repositories.topology_repository import ServiceTopologyRepository


def _seed_graph(db) -> None:
    repo = ServiceTopologyRepository(db)
    repo.upsert("payment-api", ["postgres"])
    repo.upsert("postgres", [])
    db.commit()


class TestTopologyApi:
    def test_returns_nodes_and_edges(self, client, db):
        _seed_graph(db)

        response = client.get("/api/v1/topology")

        assert response.status_code == 200
        body = response.json()
        services = {node["service"] for node in body["nodes"]}
        assert services == {"payment-api", "postgres"}
        assert {"source": "payment-api", "target": "postgres"} in body["edges"]

    def test_marks_blast_radius_of_unresolved_incident(self, client, db):
        _seed_graph(db)
        db.add(Incident(title="t", service="postgres", severity="HIGH", status="OPEN"))
        db.commit()

        response = client.get("/api/v1/topology")

        nodes = {node["service"]: node for node in response.json()["nodes"]}
        assert nodes["payment-api"]["impacted"] is True
        assert nodes["postgres"]["impacted"] is True
