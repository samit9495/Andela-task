---
title: Memory Leak / OOM
category: infrastructure
keywords: [memory, leak, oom, heap, gc, resource, cpu, host, node]
version: 1
---

# Memory Leak / Out-of-Memory

## Symptoms
- Steadily rising memory usage ending in OOM kills and pod/host restarts.
- Increasing GC pauses and degraded latency before the crash.

## Investigation
1. Inspect host and container memory utilization trends.
2. Capture a heap dump and compare object retention over time.
3. Correlate the onset with a recent deployment.

## Remediation
1. Roll back the suspect deployment if the leak is recent.
2. Increase memory limits as a temporary mitigation.
3. Fix the retention bug and add a memory regression test.
