# Nova V1 Public Launch Plan

## Current status

Nova has been moved from a local-development-only posture toward a deployable V1 release:

- Frontend lint blockers no longer prevent the production CI job.
- Render deployment configuration is committed in `render.yaml`.
- Local/runtime artifacts are excluded from Render builds.
- Production environment variables are documented in `.env.example`.
- A deployment/release guide exists in `docs/DEPLOYMENT.md`.

The remaining gates below are deployment and architecture gates. They cannot be honestly marked complete until they are verified against the real production environment.

## P0 security gates

- [ ] Every account-owned endpoint requires an authenticated server-side session.
- [ ] The legacy email-only identity compatibility path is removed.
- [ ] Browser authentication uses an HttpOnly, Secure, SameSite session cookie.
- [ ] Session expiration and logout/revocation are enforced server-side.
- [ ] Production CORS is an explicit allowlist from `NOVA_ALLOWED_ORIGINS`.
- [ ] Production secrets are supplied through environment/secret management, never source control.
- [ ] Request size and upload limits are enforced before expensive model work.
- [ ] Rate limits exist for authentication, chat, uploads, and expensive operations.
- [ ] Production errors do not expose tracebacks, model paths, prompts, tokens, or internal file paths.
- [ ] HTTPS is mandatory in the deployed environment.
- [ ] API documentation exposure is an intentional production decision.

## P0 reliability gates

- [ ] Backend health and readiness are monitored.
- [ ] NovaCore startup failure is reported as degraded readiness rather than a silent failure.
- [ ] Graceful shutdown is verified.
- [ ] User data is backed up and restore has been tested.
- [ ] Single-process/single-worker deployment is used until NovaCore becomes request-isolated.
- [ ] CI passes backend tests, frontend lint, and frontend production build.
- [ ] A two-user isolation test proves one account cannot access another account's data.

## Deployment gates

- [x] Render blueprint exists for the FastAPI backend and Vite frontend.
- [x] Production CORS and API URL variables are documented.
- [x] Ollama endpoint configuration is documented.
- [ ] A reachable production Ollama endpoint is configured.
- [ ] Persistent storage for the user database is configured and backed up.
- [ ] The deployed backend is verified healthy.
- [ ] The deployed frontend successfully reaches the backend.

## Performance gates

- Keep NovaCore lazy-loaded so `/health` can respond without loading the model.
- Avoid loading embedding/model resources on every request.
- Reuse model and embedding instances through the application lifetime.
- Serialize only the part of inference that touches shared NovaCore state.
- Never hold the NovaCore lock during unrelated I/O.
- Cache immutable knowledge/index metadata where safe.
- Bound conversation history and request sizes.
- Use streaming for long model responses.
- Compress HTTP responses at the reverse proxy where appropriate.
- Serve the React production bundle with immutable hashed assets and long cache lifetimes.
- Keep development-only logging and stack traces out of production.

## Product gates

- [ ] Login/register/logout flow works from a clean browser profile.
- [ ] Session expiry returns the user to login without stale account state.
- [ ] Chat, conversations, dashboard, settings, and memory survive normal refreshes.
- [ ] Mobile/responsive layouts are checked.
- [ ] Empty/loading/error states exist for every major screen.
- [ ] User-facing branding uses the centralized Nova logo component/configuration.
- [ ] Favicon and document metadata are configured.
- [ ] A privacy policy and terms/contact path exist before public user collection.

## Release procedure

1. Run the complete test suite.
2. Run `npm run lint` and `npm run build` in `frontend`.
3. Deploy to staging with production configuration.
4. Run smoke tests with two separate accounts.
5. Verify logs contain no secrets or passwords.
6. Verify health/readiness and rollback behavior.
7. Take a backup before the first public migration.
8. Tag the verified commit as `v1.0.0`.
9. Monitor authentication failures, latency, model errors, and HTTP 5xx responses during rollout.
