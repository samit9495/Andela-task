---
title: Database Timeout
category: database
keywords: [database, timeout, connection, pool, exhaustion, query, deadlock, sql]
version: 1
---

# Database Timeout

## Symptoms
- Errors containing "Database timeout", "connection refused", or "pool exhausted".
- Rising query latency and a spike in ERROR/CRITICAL events from a single service.

## Investigation
1. Check connection pool saturation and active connection count.
2. Identify long-running or blocking queries and lock contention.
3. Review recent schema migrations or traffic spikes.

## Remediation
1. Increase the connection pool size or add read replicas.
2. Terminate long-running queries and add missing indexes.
3. Restart the worker pool to release leaked connections.
