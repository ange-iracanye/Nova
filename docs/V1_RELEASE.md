# Nova V1 Public Release Checklist

This document separates repository checks from live-service and operator checks. Passing CI is not, by itself, a public-launch approval.

## Current repository/deployment configuration

The checked-in `render.yaml` defines two Render services in Frankfurt:

- `nova-api`: Python API using `backend.render_entry:app`, Python 3.11.9, a single Free instance, and `/health` health checks.
- `nova-frontend`: Node-based frontend build and server.
- PostgreSQL persistence is configured through the secret `NOVA_DATABASE_URL`.
- OpenRouter is configured through `OPENROUTER_API_KEY`, with `nvidia/nemotron-3-ultra:free` and `openrouter/free` as the configured model identifiers.
- The frontend/API origin values are currently set in `render.yaml`; confirm they match the live service URLs before deployment.
- The frontend lockfile is `frontend/package-lock.json`. Use `npm ci` for reproducible local/CI installs; the Render build command currently uses `npm install`.

Free-tier targets are subject to provider changes, quota limits, cold starts, and service availability. Do not describe the service as unlimited or guaranteed to remain available.

## Operator verification required

These checks require live services and cannot be proven by changing repository files alone.

1. Confirm the deployed frontend and API URLs match `render.yaml`.
2. Verify API `/health` and `/ready` behavior on the live deployment.
3. Verify a real AI response through the configured OpenRouter model.
4. Verify provider failures and exhausted free quotas fail gracefully without silently switching to paid usage.
5. Register a test account and verify login, chat, streaming, dashboard, settings, conversations, memory, uploads, and logout.
6. Create a second test account and verify it cannot read or alter the first account's data.
7. Verify account deletion removes the account and its user-owned data according to the documented retention policy.
8. Restart or allow the API to spin down, then verify accounts, sessions, conversations, memory, and learning data persist.
9. Run `python scripts/v1_smoke.py` against the live API.
10. Manually test the deployed HTTPS frontend on desktop and mobile-sized viewports.
11. Test provider errors, provider quota exhaustion, database failures, rate limits, oversized requests, and upload limits.
12. Confirm all production secrets are configured in the hosting provider, not committed to Git.
13. Review the current CI and security workflow results and resolve actionable failures.

## Privacy and legal launch blocker

`frontend/public/privacy.html` and `frontend/public/terms.html` are templates containing operator-specific placeholders. They are not final legal documents.

Before collecting public-user data, complete and review these documents for the jurisdictions in which Nova will be offered. Confirm operator identity/contact details, data collected, providers, retention, deletion, age/child safety, international transfers, jurisdiction, liability, and other applicable terms.

## Multi-instance limitation

NovaCore currently relies on a process-level lock. Keep the API at one instance until request isolation is redesigned, tested, and verified.

## Release decision

Do not call Nova publicly launched until the live infrastructure, model provider, persistence, account isolation, deletion behavior, browser flows, quota handling, and legal documents have all been verified.

After those checks pass, tag the verified commit as `v1.0.0` and publish release notes describing what was actually tested.
