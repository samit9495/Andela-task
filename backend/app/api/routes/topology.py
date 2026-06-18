"""Service topology endpoint with incident-aware blast radius."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_topology_engine
from backend.app.db.session import get_db
from backend.app.repositories.incident_repository import IncidentRepository
from backend.app.schemas.topology import TopologyEdge, TopologyNode, TopologyResponse
from backend.app.topology.topology_engine import TopologyEngine

router = APIRouter(prefix="/api/v1/topology", tags=["topology"])


@router.get("", response_model=TopologyResponse)
def get_topology(
    engine: TopologyEngine = Depends(get_topology_engine),
    db: Session = Depends(get_db),
) -> TopologyResponse:
    impacted = _impacted_services(engine, db)
    nodes = [
        TopologyNode(
            service=service,
            depends_on=engine.depends_on(service),
            impacted=service in impacted,
        )
        for service in engine.services()
    ]
    edges = [TopologyEdge(source=source, target=target) for source, target in engine.edges()]
    return TopologyResponse(nodes=nodes, edges=edges)


def _impacted_services(engine: TopologyEngine, db: Session) -> set[str]:
    impacted: set[str] = set()
    for incident in IncidentRepository(db).list_unresolved():
        if incident.service is None:
            continue
        impacted.add(incident.service)
        impacted.update(engine.blast_radius(incident.service))
    return impacted
