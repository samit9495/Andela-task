---
name: andela-fastapi-core
description: Short companion to andela-fastapi-core.mdc — quick reference for layering, dependencies, and imports when adding any backend file.
---

# Andela FastAPI Core (skill)

Companion to the rule at `.cursor/rules/andela-fastapi-core.mdc`. Use this skill when you need a quick lookup, not a full re-read of the rule.

## Layers

```
backend/app/api/routes/      <- thin handlers (parse, delegate, return)
backend/app/ingestion/       <- log ingestion + normalization
backend/app/detection/       <- statistical detection strategies
backend/app/correlation/     <- event correlation engine
backend/app/incidents/       <- incident lifecycle service
backend/app/triage/          <- agentic AI triage + LLMClient
backend/app/rag/             <- runbook RAG engine
backend/app/alerts/          <- alert engine + channels
backend/app/risk/            <- risk score engine
backend/app/repositories/    <- SQLAlchemy queries
backend/app/models/          <- ORM models
backend/app/schemas/         <- Pydantic v2 request/response models
backend/app/db/              <- engine, session, get_db dependency
backend/app/core/            <- config, domain exceptions
```

A route imports a service. A service imports repositories, engines, and the `LLMClient`. Engines do not import services. Repositories import models. Never the other way.

## Get the DB session

```python
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

def my_route(db: Session = Depends(get_db)): ...
```

## Get the LLM client

```python
from app.triage.llm_client import LLMClient, get_llm_client
from fastapi import Depends

def my_route(llm: LLMClient = Depends(get_llm_client)): ...
```

## Constructor injection in services

```python
class TriageService:
    def __init__(self, db: Session, llm: LLMClient) -> None:
        self.db = db
        self.llm = llm
```

Tests pass an in-memory session and a `FakeLLMClient`; production passes the FastAPI-managed instances. Same class.

## Pydantic v2 patterns

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    service: str = Field(max_length=100)
    level: LogLevel
    message: str = Field(max_length=4000)
    timestamp: datetime
```

## Numerical types

- Risk score, percentages exposed in API: `Decimal` with `Numeric(5, 2)` — clamp to documented ranges.
- Detection math (z-score, EWMA, mean/stddev): `numpy` floats internally; convert at the boundary.

## Time

All timestamps stored and exchanged as **timezone-aware UTC**.

## See also

- Rule: `.cursor/rules/andela-fastapi-core.mdc`
- Skill: `.cursor/skills/scaffold-api-endpoint/SKILL.md`
- Skill: `.cursor/skills/scaffold-service-layer/SKILL.md`
- Rule: `.cursor/rules/andela-agentic-ai.mdc` (LLMClient design)
