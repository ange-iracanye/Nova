# Nova V1 Public Launch Plan

## Current status

Nova V1 is configured for a public single-instance Render deployment using OpenRouter for AI inference and PostgreSQL persistence. The repository now contains production CORS hardening, secure session cookies, request IDs, security headers including CSP, account deletion, disabled production demo mode, and finalized operational drafts for the Privacy Notice and Terms of Service.

The remaining gates below require either real production credentials/environment access or an operator decision/review that cannot be verified from source control alone.

## Selected V1 product decisions

- AI provider: OpenRouter.
- Primary model: `nvidia/nemotron-3-ultra:free`.
- Fallback: `openrouter/free`.
- Public demo: disabled for V1.
- Minimum user age: 16.
- Account deletion: immediate user-requested deletion of account-owned application data where technically available.
- Memory controls: users should be able to clear memory independently of deleting the account.
- Intended database: Supabase PostgreSQL via `NOVA_DATABASE_URL`.
- Operator: Iracanye Ange-Michaël, France.
- Privacy contact: `iracanyemichael@gmail.com`.

## P0 security gates

- [x] Production CORS requires explicit HTTPS origins.
- [x] Browser authentication uses HttpOnly production cookies.
- [x] Persistent server-side sessions are used in the production entrypoint.
- [x] Production request IDs are returned as `X-Request-ID`.
- [x] Request size and upload limits are enforced before expensive work.
- [x] Authentication and chat rate limits exist.
- [x] Production API documentation is disabled by default.
- [x] Security headers and a production CSP are installed.
- [x] Account deletion removes the account, matching sessions, persisted conversations and user memory where those stores are available.
- [ ] Remove the legacy email-only identity compatibility path from every account-owned endpoint.
- [ ] Complete a CSRF review of every cookie-authenticated state-changing endpoint.
- [ ] Verify upload MIME/type validation and path traversal defenses against malicious inputs.
- [ ] Verify that no secret, token, password, prompt or sensitive user content is written to logs.

## P0 reliability gates

- [x] Render is pinned to one backend instance because NovaCore remains process-stateful.
- [x] Health and readiness endpoints exist.
- [x] Production startup keeps NovaCore lazy-loaded.
- [x] OpenRouter is the sole configured V1 provider family and the fallback is also free-tier oriented.
- [ ] Verify the real OpenRouter key and both model paths in production.
- [ ] Verify provider quota exhaustion returns a safe user-facing error and never silently creates paid usage.
- [ ] Verify PostgreSQL persistence after a real Render restart/redeploy.
- [ ] Verify two-user isolation against direct API requests, not only UI behavior.
- [ ] Verify account deletion end-to-end in the deployed environment.
- [ ] Run the full CI suite after the final hardening changes.

## Database

The repository is already wired for PostgreSQL through `NOVA_DATABASE_URL`, and the Render blueprint declares that variable as a secret (`sync: false`). Source control cannot reveal whether the real Render secret is currently populated or whether the existing database is the intended Supabase project. Verify that in the Render dashboard without committing the connection string.

## Product gates

- [ ] Registration enforces the 16+ policy server-side and presents the policy clearly in the frontend.
- [ ] Login/register/logout works from a clean browser profile.
- [ ] Session expiry returns the user to login without stale account state.
- [ ] Chat, conversations, dashboard, settings, memory and uploads survive normal refreshes.
- [ ] Users can clear Nova memory independently from account deletion.
- [ ] Account deletion is reachable from the authenticated UI and clears local authentication state.
- [ ] Mobile/responsive layouts are checked.
- [ ] Empty/loading/error states exist for every major screen.
- [ ] Favicon and document metadata are configured.
- [ ] Privacy Notice and Terms are reviewed for French/EU requirements before public collection.

## Production gates

- [ ] Configure `OPENROUTER_API_KEY` in Render.
- [ ] Configure/verify `NOVA_DATABASE_URL` in Render.
- [ ] Verify `NOVA_ALLOWED_ORIGINS` exactly matches the deployed frontend origin.
- [ ] Deploy the exact verified commit.
- [ ] Check `/health` and `/ready` over HTTPS.
- [ ] Run the two-account production smoke test.
- [ ] Run a real chat and streaming response.
- [ ] Verify persistence after restart/redeploy.
- [ ] Verify no secrets appear in Render/GitHub logs.
- [ ] Verify rollback to the previous known-good deployment.
- [ ] Only after all gates pass, tag `v1.0.0`.

## Release procedure

1. Run the complete test suite.
2. Run `npm run lint` and `npm run build` in `frontend`.
3. Deploy with the production environment variables.
4. Run the production smoke/E2E checks with two separate accounts.
5. Verify account isolation and deletion.
6. Verify OpenRouter model/fallback behavior and free-only cost safety.
7. Verify health/readiness, persistence and rollback behavior.
8. Review the Privacy Notice and Terms for the actual deployment/provider configuration.
9. Take a backup before the first public migration.
10. Tag the verified commit as `v1.0.0`.
11. Monitor authentication failures, latency, model errors, quota failures and HTTP 5xx responses during rollout.
