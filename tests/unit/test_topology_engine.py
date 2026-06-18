"""Unit tests for the TopologyEngine (pure graph logic)."""

from backend.app.topology.topology_engine import TopologyEngine

_ADJ = {
    "checkout-service": ["payment-api", "auth-service"],
    "payment-api": ["postgres", "auth-service"],
    "auth-service": ["postgres"],
    "postgres": [],
}


class TestTopologyEngine:
    def test_services_includes_all_nodes(self):
        engine = TopologyEngine(_ADJ)

        assert set(engine.services()) == {
            "checkout-service",
            "payment-api",
            "auth-service",
            "postgres",
        }

    def test_edges_point_from_service_to_dependency(self):
        engine = TopologyEngine(_ADJ)

        assert ("payment-api", "postgres") in engine.edges()
        assert ("checkout-service", "auth-service") in engine.edges()

    def test_blast_radius_is_transitive_dependents(self):
        engine = TopologyEngine(_ADJ)

        assert engine.blast_radius("postgres") == {
            "auth-service",
            "payment-api",
            "checkout-service",
        }

    def test_leaf_consumer_has_empty_blast_radius(self):
        engine = TopologyEngine(_ADJ)

        assert engine.blast_radius("checkout-service") == set()

    def test_unknown_service_has_empty_blast_radius(self):
        engine = TopologyEngine(_ADJ)

        assert engine.blast_radius("does-not-exist") == set()

    def test_root_service_is_the_most_upstream(self):
        engine = TopologyEngine(_ADJ)

        root = engine.root_service({"payment-api", "postgres", "checkout-service"})

        assert root == "postgres"

    def test_root_service_none_when_no_known_services(self):
        engine = TopologyEngine(_ADJ)

        assert engine.root_service({"ghost"}) is None
