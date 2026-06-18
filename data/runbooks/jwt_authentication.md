---
title: Authentication Failures
category: authentication
keywords: [authentication, auth, jwt, token, login, credential, 401, 403, identity]
version: 1
---

# Authentication Failures

## Symptoms
- Surge in 401/403 responses and "invalid token" or "login failed" errors.
- Failures concentrated at the auth or gateway service.

## Investigation
1. Verify the identity provider availability and token signing keys.
2. Check for expired secrets, rotated keys, or clock skew.
3. Review recent changes to auth middleware or JWT configuration.

## Remediation
1. Restore or rotate the correct token signing keys.
2. Synchronize clocks across auth services (NTP).
3. Roll back recent auth configuration changes.
