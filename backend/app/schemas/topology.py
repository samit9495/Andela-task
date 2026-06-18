"""Schemas for the service topology API."""

from pydantic import BaseModel, ConfigDict


class TopologyNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service: str
    depends_on: list[str]
    impacted: bool = False


class TopologyEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    target: str


class TopologyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
