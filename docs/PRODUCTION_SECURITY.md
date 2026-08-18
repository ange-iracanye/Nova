# Nova V1 Production Security Checklist

## Implemented for the single-instance V1 deployment

- Salted scrypt password hashes
- Legacy SHA-256 password migration after successful login
- Constant-time password comparisons
- Atomic authentication database writes
- Fail-closed handling of corrupted user data
- Password complexity policy for new registrations
- Process-local login throttling after repeated failures
- Session expiration and explicit logout endpoints
- SQLite-backed persistent authentication sessions for the production deployment
- Request validation models for API payload sizes
- Exact deployment CORS configuration via `NOVA_ALLOWED_ORIGINS`
- Production authentication boundary requiring a real session for account/data endpoints
- Public health/readiness/status endpoints for deployment monitoring
- Security headers including `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, Permissions Policy, and HSTS in production
- No internal exception text returned by the API's global error response
- GitHub Actions CI for backend compilation/tests and frontend install/lint/build
- Production Render Blueprint with a single backend instance and persistent data disk
- Secrets kept in deployment environment variables rather than Git

## V1 architecture boundary

Nova's API still contains a legacy compatibility path where local development can
identify an account by an email field. **This path is disabled as an access
mechanism in production by `backend/production.py`.** Public account/data routes
require a valid Nova session before the request reaches the endpoint.

The production entrypoint also replaces the API's in-memory authentication
session mapping with `PersistentSessionStore`, backed by SQLite on the Render
persistent disk. V1 therefore remains intentionally single-instance because
NovaCore has shared runtime state protected by `nova_process_lock`.

## Intentionally deferred hardening

These items are not prerequisites for the first controlled public V1 release,
but should be addressed before scaling Nova substantially:

- HttpOnly cookie-based authentication instead of browser-readable bearer/session storage
- CSRF protection if cookie authentication is introduced across origins
- Account recovery and password-reset flows
- IP-aware rate limiting at the reverse-proxy/API layer
- Multi-worker/shared-session architecture
- Request IDs and structured centralized logging
- Upload CPU/memory/time limits and stricter file-type quotas
- Monitoring/alerting and automated backup/restore procedures
- Automated end-to-end tests against the deployed production URLs

## Deployment rules

- Run Nova behind HTTPS.
- Store `OLLAMA_API_KEY`, `NOVA_ALLOWED_ORIGINS`, and `VITE_API_URL` in deployment secrets/configuration.
- Never commit `.env` files or model/API credentials.
- Keep user data and memory stores on the persistent application disk, not in frontend build artifacts.
- Keep the backend at one instance until NovaCore request state is fully isolated.

## Release gate

Nova V1 is considered **code/deployment ready** when:

1. GitHub Actions passes backend tests and frontend build/lint.
2. Render successfully deploys both services.
3. `/health` returns healthy and `/ready` becomes ready.
4. A new user can register and log in.
5. The browser receives and uses the returned Nova session.
6. Chat works through Ollama Cloud.
7. Conversations, settings, dashboard, memory, upload, and logout work for the authenticated user.
8. A second account cannot access the first account's data.
9. Restarting the backend does not erase registered users or active persistent sessions.
10. The deployed frontend can reach the deployed backend over HTTPS.
