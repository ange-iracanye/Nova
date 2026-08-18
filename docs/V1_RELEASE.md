# Nova V1 Public Release

## What is already configured in Git

- FastAPI production entrypoint: `backend/production.py`
- Persistent user database on the Render disk
- SQLite-backed persistent authentication sessions
- Production CORS allowlist
- Production authentication boundary
- Security headers and HTTPS HSTS
- Single-instance backend deployment to preserve NovaCore runtime safety
- Render Blueprint for backend + frontend
- Ollama Cloud environment configuration
- 10 GB persistent application disk
- Python 3.11.9 deployment target
- Frontend production build configuration
- GitHub Actions backend/frontend CI
- Authentication and persistent-session regression tests
- Production security/release checklist
- ESLint V1 policy that keeps advisory React migration diagnostics from blocking the production build while preserving real JavaScript errors

## External launch actions

These cannot be safely committed to GitHub because they are deployment secrets or account actions:

1. Create/connect the Render deployment from the repository's `render.yaml`.
2. Provide `OLLAMA_API_KEY` as a Render secret.
3. Set `NOVA_ALLOWED_ORIGINS` to the exact HTTPS URL of the deployed frontend.
4. Set `VITE_API_URL` to the exact HTTPS URL of the deployed API.
5. Deploy both services.
6. Verify `/health` and `/ready` on the API.
7. Register a test account.
8. Log in and verify chat, streaming, dashboard, settings, conversations, memory, upload, and logout.
9. Create a second test account and verify that the first account's data is not visible.
10. Restart/redeploy the backend and verify that users and persistent sessions remain available.

## Release decision

Do not label Nova V1 publicly launched until the live smoke test above passes. The Git repository can be deployment-ready while the service is still waiting for external credentials and live infrastructure verification.
