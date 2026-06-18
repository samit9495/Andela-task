---
name: andela-testing
description: Short companion for testing — pytest fixtures, FakeLLMClient, AI evaluation suite shape. Use when writing or reviewing tests.
---

# Andela Testing (skill)

Companion to `.cursor/rules/andela-testing.mdc`.

## The 4 test directories

```
tests/
├── unit/         # default, fast, in-memory SQLite. Detection math, services.
├── integration/  # FastAPI TestClient + DB. End-to-end pipelines.
├── ai_eval/      # @pytest.mark.ai_eval — uses recorded/canned LLM responses
└── sdk/          # SDK tests against mocked HTTP
```

## Standard fixtures (`tests/conftest.py`)

```python
@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db(engine) -> Session:
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def fake_llm() -> FakeLLMClient:
    return FakeLLMClient()
```

## FakeLLMClient

```python
class FakeLLMClient:
    """Deterministic LLM fake. Maps a prompt-hash to a canned structured output."""
    def __init__(self):
        self._responses: dict[str, BaseModel] = {}

    def register(self, prompt_hash: str, response: BaseModel) -> None:
        self._responses[prompt_hash] = response

    def complete_structured(self, *, prompt, schema, **kwargs):
        key = sha256(prompt.encode()).hexdigest()
        if key not in self._responses:
            raise AssertionError(f"FakeLLM has no response for {key[:8]}; did you forget to register?")
        return self._responses[key]
```

## Naming

- Files: `test_<module>.py`.
- Classes: `class TestZScoreDetector:`.
- Methods: `test_<action>_<condition>_<expected>`.

## What to mock vs not mock

| Boundary | Mock? |
|----------|-------|
| `time.time` / `datetime.now` | Yes (inject a clock) |
| `random` | Yes (seed it) |
| Filesystem | Yes (use `tmp_path`) |
| Network / HTTP outbound | Yes |
| **Gemini client (`LLMClient`)** | Yes (use `FakeLLMClient`) |
| Your own `EventRepository` | No (use real in-memory DB) |
| Your own `DetectionEngine` | No (use real with small fixtures) |

## AI evaluation tests

- Marker: `@pytest.mark.ai_eval`.
- Run separately in CI; not part of the inner TDD loop.
- Use recorded LLM responses or `FakeLLMClient` with pre-registered fixtures.
- Each scenario lives in `tests/ai_eval/fixtures/<scenario>.json`.
- Output an evaluation report (e.g., `docs/ai_evaluations.md`) with metrics per scenario.

## Coverage

- Target: ≥ 90% on changed modules.
- `pytest --cov=backend/app --cov-report=term-missing`.

## See also

- Rule: `.cursor/rules/andela-testing.mdc`
- Rule: `.cursor/rules/andela-tdd-discipline.mdc`
- Rule: `.cursor/rules/andela-agentic-ai.mdc` (LLMClient + structured outputs)
- Skill: `.cursor/skills/andela-tdd-loop/SKILL.md`
