---
name: sql-query-audit
description: Audit SQLAlchemy queries and raw SQL for injection risk and ORM safety. Use when asked to audit SQL, fix unsafe queries, or before touching backend/app/repositories or backend/app/db.
---

# SQL Query Audit (SQLAlchemy + SQLite)

## Trigger

Use when asked to: SQL audit, SQL injection, parameterized queries, raw SQL, fix unsafe SQL, review repositories.

## Context

The project uses SQLAlchemy 2.x ORM by default over SQLite. Raw SQL is only used when the ORM is genuinely awkward. This skill systematically finds and fixes unsafe patterns and reviews ORM usage.

## Step 1 — Search for unsafe patterns

Use Cursor's Grep tool (NOT terminal `grep`):

```
# f-strings or .format() near SQL primitives
pattern: text\(f["\']
glob: backend/**/*.py

pattern: text\(.+\.format\(
glob: backend/**/*.py

# raw execute with string concatenation
pattern: execute\(.+\+.+\)
glob: backend/**/*.py

# direct string interpolation into select / insert / update / delete strings
pattern: f"(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)
glob: backend/**/*.py
```

## Step 2 — Classify each hit

For every match decide:

- **Value parameter** ⇒ must use a bound parameter.
- **Identifier (table/column)** ⇒ never user-controlled; if dynamic, validate against an allow-list and use SQLAlchemy `bindparam(..., literal_execute=True)` or `sqlalchemy.sql.quoted_name`.
- **Static SQL fragment** ⇒ safe, but consider converting to ORM.

## Step 3 — Fix patterns

### Pattern A — f-string with values ⇒ bound params

```python
# BAD
db.execute(text(f"SELECT * FROM events WHERE service = '{service}'"))

# GOOD (raw text)
db.execute(text("SELECT * FROM events WHERE service = :service"), {"service": service})

# BETTER (ORM)
db.scalars(select(Event).where(Event.service == service)).all()
```

### Pattern B — `.format()` ⇒ same fix

```python
# BAD
db.execute(text("SELECT * FROM incidents WHERE id = {}".format(incident_id)))

# GOOD
db.execute(text("SELECT * FROM incidents WHERE id = :id"), {"id": incident_id})
```

### Pattern C — `IN (...)` with tuple interpolation

```python
# BAD
db.execute(text(f"SELECT * FROM anomalies WHERE id IN {tuple(ids)}"))

# GOOD (ORM)
db.scalars(select(Anomaly).where(Anomaly.id.in_(ids))).all()

# GOOD (raw text with expanding bindparam)
from sqlalchemy import text, bindparam
stmt = text("SELECT * FROM anomalies WHERE id IN :ids").bindparams(bindparam("ids", expanding=True))
db.execute(stmt, {"ids": ids})
```

### Pattern D — Dynamic ORDER BY / column names

Never accept a raw column name from the client.

```python
ALLOWED_SORT = {
    "timestamp": Event.timestamp,
    "level": Event.level,
    "service": Event.service,
}

def list_sorted(self, sort_by: str = "timestamp"):
    column = ALLOWED_SORT.get(sort_by)
    if column is None:
        raise InvalidSortField(sort_by)
    return self.db.scalars(select(Event).order_by(column.desc())).all()
```

### Pattern E — Bulk insert (batch ingestion)

```python
# GOOD (parameterized, fast)
db.execute(insert(Event), [{"service": ..., "level": ..., ...} for ... in events])
db.commit()
```

The list-of-dicts form goes through `executemany` with bound parameters.

## Step 4 — Detect ORM smells

- **N+1**: a list endpoint iterating models that lazy-load a relationship. Add `selectinload(Incident.anomalies)` to the select.
- **Implicit conversions**: comparing `Decimal` to a `float`. Always pass `Decimal` into the query.
- **Hard-coded `LIMIT 1000`** when the API contract is `LIMIT 50`. Push the value to the query parameter.

## Step 5 — Add a test for any fix

Each fix gets a RED test first:

```python
def test_list_events_does_not_break_on_apostrophe_in_service(db, client):
    db.add(Event(service="payment-api", level="ERROR", message="ok",
                 signature="ok", timestamp=now()))
    db.commit()
    resp = client.get("/api/v1/events", params={"service": "X'); DROP TABLE events;--"})
    assert resp.status_code == 200
    assert resp.json() == []
    # Sanity: the table still exists
    assert db.scalar(select(func.count(Event.id))) == 1
```

## Checklist

- [ ] No f-strings or `.format()` around SQL text
- [ ] All values use bound parameters
- [ ] All identifiers come from an allow-list (or the ORM)
- [ ] Bulk operations use executemany via `insert(Model), [dict, ...]`
- [ ] One regression test per fix
- [ ] No `text(...)` call introduces a new injection surface

## See also

- `.cursor/rules/andela-sql-safety.mdc`
- `.cursor/rules/andela-security.mdc`
- `.cursor/skills/security-audit/SKILL.md`
