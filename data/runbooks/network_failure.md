---
title: Network / Dependency Failure
category: network
keywords: [network, dns, connection, refused, unreachable, socket, dependency, upstream, latency]
version: 1
---

# Network / Dependency Failure

## Symptoms
- "Connection refused", DNS resolution errors, or upstream timeouts.
- Errors spanning multiple services that share a dependency.

## Investigation
1. Check DNS resolution and upstream service reachability.
2. Review recent network, firewall, or service-mesh changes.
3. Inspect the dependency's own health and error rate.

## Remediation
1. Fail over to a healthy replica or region.
2. Roll back recent network or firewall configuration changes.
3. Add retries with backoff and circuit breakers to callers.
