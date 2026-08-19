# Nova V1 Public Release

## Repository-side readiness

The repository contains the production application, authentication/session hardening, frontend build, CI checks, production security tests, Render deployment configuration, and a live two-account smoke-test script.

Current deployment assumptions:

- Render backend: single `starter` instance in Frankfurt;
- Render backend: 10 GB persistent disk mounted at `/opt/render/project/src/data`;
- persistent users database: `${NOVA_DATA_DIR}/users.json`;
- persistent sessions database: `${NOVA_SESSION_DB}`;
- frontend: Render static site;
- production API docs and demo endpoints disabled by default;
- production CORS restricted to the exact frontend HTTPS origin;
- Ollama Cloud configured through Render secrets;
- Python 3.11.9;
- frontend deploy uses `npm install` because this repository intentionally does not currently contain a package-lock file.

## Actions that require the operator

These cannot be completed safely by repository edits alone:

1. Create/connect the Render deployment from `render.yaml`.
2. Confirm the Render service is using the persistent disk declared in `render.yaml`.
3. Provide `OLLAMA_API_KEY` as a Render secret.
4. Set `NOVA_ALLOWED_ORIGINS` to the exact HTTPS URL of the deployed frontend.
5. Set `VITE_API_URL` to the exact HTTPS URL of the deployed API.
6. Deploy both services.
7. Verify `/health` and `/ready` on the live API.
8. Verify the configured Ollama Cloud model is reachable and Nova can produce a real answer.
9. Register a test account and verify login, chat, streaming, dashboard, settings, conversations, memory, upload, and logout.
10. Create a second test account and verify that the first account's data is not visible to it.
11. Restart/redeploy the backend and verify that users, sessions, and relevant persisted data remain available.
12. Run `scripts/v1_smoke.py` against the live API.
13. Complete a manual browser test of the frontend on the deployed HTTPS URL.
14. Replace every placeholder in `frontend/public/privacy.html` and `frontend/public/terms.html` with final operator/legal information and complete the required legal review before public registration.
15. Decide and document the actual retention, deletion, age/child-safety, international-transfer, third-party-provider, and user-content rules used by the service.
16. Review open dependency-update PRs and merge any required security/compatibility updates before the final release commit.
17. Back up the production persistent data according to your chosen operational policy.

## Privacy and legal launch blocker

`frontend/public/privacy.html` and `frontend/public/terms.html` are intentionally templates and must **not** be treated as final legal documents. They contain operator-specific placeholders for identity, contact details, retention, providers, age/child safety, transfers, jurisdiction, liability, deletion, and other terms.

Do not collect public-user data until those documents are completed and reviewed for the jurisdictions in which Nova will be offered.

## Release decision

Do not label Nova V1 publicly launched until all operator actions above that apply to the deployment have passed. A green GitHub build only proves repository checks; it does not prove production infrastructure, third-party model availability, persistence after restart, browser behavior, or legal readiness.

Once the live checks pass, tag the verified commit as `v1.0.0` and publish the release notes.
