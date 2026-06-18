---
title: Disk Full
category: infrastructure
keywords: [disk, storage, full, space, volume, inode, write, filesystem]
version: 1
---

# Disk Full

## Symptoms
- "No space left on device" errors and failed writes.
- Log shipping or database writes failing on a single host.

## Investigation
1. Identify the largest directories and growth rate.
2. Check for runaway log files or unrotated artifacts.
3. Inspect inode exhaustion separately from byte capacity.

## Remediation
1. Rotate and compress or ship logs off the host.
2. Expand the volume or attach additional storage.
3. Add disk-usage alerts below the saturation threshold.
