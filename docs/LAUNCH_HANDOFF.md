# Nova V1 Launch Handoff

## Decisions locked for V1

- AI provider: OpenRouter
- Primary model: `nvidia/nemotron-3-ultra:free`
- Fallback: `openrouter/free`
- Public demo: disabled
- Minimum age: 16+
- Registration verifies date of birth, but Nova does not retain the date of birth
- Account deletion: permanent
- Memory deletion: available independently from account deletion
- Database: PostgreSQL/Supabase-compatible connection through `NOVA_DATABASE_URL`
- Operator: Iracanye Ange-Michaël
- Country: France
- Privacy/contact email: `iracanyemichael@gmail.com`
- Postal address: intentionally not published in V1 repository pages

## Repository-side hardening completed

- OpenRouter production configuration aligned across deployment/docs.
- Production CORS requires explicitly configured HTTPS origins.
- Production request IDs are returned through `X-Request-ID`.
- Production API paths require authentication except the explicit public allowlist.
- Public demo is disabled in the Render configuration.
- Public API documentation is not part of the production public allowlist.
- CSP and additional security headers are installed by the production entrypoint.
- Per-user settings are isolated by a SHA-256-derived user directory.
- Per-user settings are removed during account deletion.
- Long-term memory can be cleared without deleting the account.
- Account deletion removes the database account, legacy local account copy, sessions, memory, settings and persisted conversations handled by V1.
- Production registration has a server-side 16+ age gate and does not store DOB.
- Production sessions use PostgreSQL when `NOVA_DATABASE_URL` is configured, avoiding dependence on Render's ephemeral filesystem.
- Production preflight checks protect the free-model/cost-safety invariant.
- Regression tests cover production configuration and preflight safeguards.

## Operator-only steps before opening public registration

These cannot be verified from GitHub repository access alone:

1. In Render, set `OPENROUTER_API_KEY` as a secret.
2. In Render, set `NOVA_DATABASE_URL` to the intended Supabase/PostgreSQL connection string.
3. Confirm `NOVA_ALLOWED_ORIGINS` exactly matches the production frontend HTTPS origin.
4. Keep `NOVA_ENABLE_DEMO=false`.
5. Keep `NOVA_ENABLE_DOCS=false`.
6. Deploy the current `main` commit.
7. Run `python scripts/production_preflight.py` against the production environment variables, or verify the same invariants manually.
8. Verify `/health` returns healthy and `/ready` returns ready.
9. Register two test accounts, including one account that is exactly 16 years old and one under 16. Confirm the under-16 registration is rejected by the server.
10. Verify login, chat, streaming, settings, memory, conversations, logout and account deletion.
11. Restart/redeploy the backend and verify the account session/database state behaves as expected.
12. Confirm an OpenRouter request succeeds with the configured free model and that a provider failure does not switch to a paid model.
13. Only after these checks, enable public registration/announce the V1 launch.

## Important limitations

- The repository cannot reveal Render secret values through GitHub access.
- The repository cannot prove that the configured Supabase database is reachable until the deployed service connects to it.
- Legal pages are operational V1 drafts and should receive appropriate French/EU legal review before public launch.
- Nova V1 intentionally remains single-instance because NovaCore uses process-level request serialization.
