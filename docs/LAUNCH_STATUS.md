# Nova V1 Public Launch Status

Last reviewed: 2026-08-24

## Repository hardening completed

- OpenRouter is the production LLM provider.
- Primary free model: `nvidia/nemotron-3-ultra:free`.
- Fallback: `openrouter/free`.
- Public demo disabled in production.
- API documentation disabled in production.
- Production CORS requires explicit HTTPS origins.
- Production security headers are enabled.
- Request IDs are attached to responses.
- Request and upload size limits are enforced.
- Authentication endpoints and destructive privacy endpoints are rate limited.
- 16+ registration policy is enforced server-side with date-of-birth validation; the DOB is not persisted by Nova.
- Settings are isolated per user.
- Users can clear long-term memory independently.
- Users can permanently delete their account and account-owned data.
- Production session storage uses PostgreSQL when `NOVA_DATABASE_URL` is configured.
- Render uses a lightweight boot layer so health checks bind before the ML runtime initializes.
- Automated backend/frontend CI is configured.
- Automated CodeQL and Python dependency-audit workflows are configured.
- A public security contact policy is available at `/.well-known/security.txt`.

## Remaining operator-side launch checks

These cannot be completed through the public GitHub repository alone because they depend on private service configuration or a real deployment:

1. Set `NOVA_DATABASE_URL` in Render to the correct Supabase PostgreSQL connection string.
2. Set `OPENROUTER_API_KEY` in Render.
3. Confirm `NOVA_ALLOWED_ORIGINS` exactly matches the deployed frontend origin.
4. Deploy the latest `main` commit.
5. Confirm `/health` returns HTTP 200.
6. Confirm `/` returns HTTP 200 rather than the database-unavailable 503 seen when PostgreSQL credentials are invalid.
7. Register an account with a valid age of at least 16.
8. Confirm an under-16 registration is rejected.
9. Confirm chat uses OpenRouter and does not require Ollama.
10. Confirm two accounts cannot see each other's settings, memory, or conversations.
11. Confirm memory deletion works.
12. Confirm account deletion removes the account and session.
13. Confirm a fresh deployment preserves PostgreSQL-backed sessions/data.
14. Confirm the GitHub CI and security workflows are green.

## Launch gate

Nova should not be advertised as publicly launch-ready until the operator-side checks above pass in the real Render/Supabase/OpenRouter environment.
