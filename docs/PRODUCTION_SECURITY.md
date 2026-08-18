# Nova V1 Production Security Checklist

## Implemented

- Salted scrypt password hashes
- Legacy SHA-256 password migration after successful login
- Constant-time password comparisons
- Atomic authentication database writes
- Fail-closed handling of corrupted user data
- Password complexity policy for new registrations
- Process-local login throttling after repeated failures
- Session expiration and explicit logout endpoints
- Request validation models for API payload sizes
- GitHub Actions CI
- CodeQL scanning
- Dependabot dependency monitoring
- Reusable security boundary helpers for HttpOnly session cookies, exact CORS origins, request IDs, security headers, and authenticated identity checks
- `.env.example` documenting production environment configuration

## Security boundary integration gate

The reusable helpers in `backend/security.py` are intentionally isolated so the API authentication migration can be wired without duplicating security logic. Before public deployment, the API must call these helpers from its middleware/authentication path.

### API boundary

- Remove the unauthenticated email compatibility path in `resolve_user_email()`.
- Require an authenticated session for every account-owned endpoint.
- Verify that the authenticated session user owns every requested conversation/resource.
- Replace wildcard HTTP methods/headers in CORS with the exact methods and headers used by the frontend.
- Set production CORS origins from `NOVA_ALLOWED_ORIGINS`. Do not ship localhost origins as the production allowlist.
- Apply security headers such as `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, Permissions Policy, and HSTS when HTTPS is guaranteed.
- Disable `/docs`, `/redoc`, and `/openapi.json` in production unless they are intentionally exposed.
- Add a request ID and structured server logging.
- Never return internal exception text to clients.

### Authentication

- Wire `set_session_cookie()` into successful login/registration responses.
- Wire `clear_session_cookie()` into logout.
- Resolve browser authentication from the HttpOnly cookie before considering an Authorization bearer token.
- Stop storing bearer tokens in persistent JavaScript-readable storage once cookie authentication is active.
- Move session state from the process into a shared store before using multiple backend workers/instances.
- Add CSRF protection if cookie authentication is introduced across origins. SameSite=Lax reduces risk but does not replace a deliberate CSRF policy for every deployment topology.
- Add account-level and IP-aware login throttling at the reverse-proxy/API layer.
- Consider password-reset and account-recovery flows before accepting real users.

### NovaCore

NovaCore currently has shared runtime state protected by `nova_process_lock`. Keep this lock until processing is made request-isolated. Removing it prematurely can allow one user's runtime context to race with another user's request.

### Deployment

- Run behind HTTPS and a reverse proxy.
- Bind the application to the private/container interface rather than exposing a development server directly to the internet.
- Store secrets in deployment secret management, never in Git.
- Keep `data/users.json` and user memory outside the repository and outside public build artifacts.
- Back up user data securely and test restoration.
- Add CPU/memory/time limits around model inference and uploads.
- Add monitoring for repeated 4xx/5xx responses and inference failures.

## Current architecture limitation

Nova's authentication session dictionary and demo-session dictionary live in process memory. This is acceptable for a single-process V1 deployment, but sessions disappear on restart and are not shared between workers. Treat multi-worker deployment as a separate hardening milestone.
