# Nova V1 Public Release

## Repository-side readiness

Nova V1 is configured for a $0/month deployment using a free Render web service, a free PostgreSQL database, and the Gemini Developer API free tier. Render's free filesystem is treated as ephemeral; runtime user data is restored from PostgreSQL at startup and periodically synchronized back to it.

Current deployment assumptions:

- Render backend: single Free instance in Frankfurt;
- Render frontend: Free static site;
- free PostgreSQL persistence through `NOVA_DATABASE_URL`;
- free Gemini AI through `GEMINI_API_KEY`;
- production model: `gemini-3.1-flash-lite`;
- production API docs and demo endpoints disabled by default;
- production CORS restricted to the exact frontend HTTPS origin;
- Python 3.11.9;
- frontend deploy uses `npm install` because this repository intentionally does not currently contain a package-lock file.

## Operator actions

These cannot be completed safely by repository edits alone:

1. Create a free Supabase project and copy its PostgreSQL connection string.
2. Create a free Gemini API key with access to the configured free-tier model.
3. Create/connect the Render deployment from `render.yaml`.
4. Add `NOVA_DATABASE_URL` as a Render secret.
5. Add `GEMINI_API_KEY` as a Render secret.
6. Set `NOVA_ALLOWED_ORIGINS` to the exact HTTPS URL of the deployed frontend.
7. Set `VITE_API_URL` to the exact HTTPS URL of the deployed API.
8. Deploy both services.
9. Verify `/health` and `/ready` on the live API.
10. Verify that Nova can produce a real answer through Gemini.
11. Register a test account and verify login, chat, streaming, dashboard, settings, conversations, memory, upload, and logout.
12. Create a second test account and verify that the first account's data is not visible to it.
13. Let the API restart/spin down, then verify that accounts, sessions, conversations, memory, and learning data are restored.
14. Run `scripts/v1_smoke.py` against the live API.
15. Complete a manual browser test of the deployed HTTPS frontend.
16. Replace every placeholder in `frontend/public/privacy.html` and `frontend/public/terms.html` with final operator/legal information and complete the required legal review before public registration.
17. Review the free-provider quotas before public promotion. Free hosting and free AI tiers are quota-limited and can stop serving requests when their limits are reached.

## Free-tier limitations

This architecture intentionally avoids a paid server, paid disk, and paid model API. That does **not** mean unlimited compute is available. Render Free can spin down after inactivity and has monthly usage limits. Supabase Free provides limited database capacity and can pause inactive projects. Gemini's free tier has model-specific rate limits. If those quotas are exhausted, Nova must fail gracefully rather than silently switching to a paid provider.

## Privacy and legal launch blocker

`frontend/public/privacy.html` and `frontend/public/terms.html` are templates and must **not** be treated as final legal documents. They contain operator-specific placeholders for identity, contact details, retention, providers, age/child safety, transfers, jurisdiction, liability, deletion, and other terms.

Do not collect public-user data until those documents are completed and reviewed for the jurisdictions in which Nova will be offered.

## Release decision

A green GitHub build proves repository checks only. Before calling Nova V1 publicly launched, verify the live infrastructure, free AI provider, persistence after restart, account isolation, browser behavior, quota behavior, and legal documents.

Once the live checks pass, tag the verified commit as `v1.0.0` and publish the release notes.
