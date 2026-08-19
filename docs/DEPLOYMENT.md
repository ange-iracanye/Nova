# Nova V1 deployment

Nova has a deployment blueprint for Render in `render.yaml`.

## Services

The blueprint creates:

- `nova-api`: FastAPI/Uvicorn backend
- `nova-frontend`: Vite production static site

## Required production environment variables

### Backend

- `NOVA_ENV=production`
- `NOVA_ALLOWED_ORIGINS=https://<your-frontend-domain>`
- `OLLAMA_HOST=https://ollama.com` (or another reachable Ollama-compatible endpoint)
- `OLLAMA_API_KEY=<secret>
- `OLLAMA_MODEL=<production model>`

### Frontend

- `VITE_API_URL=https://<your-api-domain>`

### Render persistence

The API service is intentionally single-instance for V1 and mounts a persistent disk at `/opt/render/project/src/data`. The session database and user data are stored there. Do not enable horizontal scaling until the session store and user data store are moved to shared durable infrastructure.

## Production security defaults

The production entrypoint now fails closed when `NOVA_ALLOWED_ORIGINS` is missing or contains non-HTTPS origins. Interactive API documentation and demo endpoints are disabled by default in production and must be explicitly enabled with `NOVA_ENABLE_DOCS=true` or `NOVA_ENABLE_DEMO=true`.

The backend also enforces request-size limits, authentication boundaries, session cookies, security headers, and lightweight per-IP rate limits. These are V1 safeguards, not a substitute for a managed distributed rate limiter at larger scale.

## Important V1 architecture constraint

Nova's current LLM layer uses Ollama. The production backend therefore needs an Ollama endpoint that is reachable from the deployed server. A local Ollama process on a developer laptop is not a production dependency.

## Release gate

Do not mark the service as a fully hardened public release until these are completed in the deployed environment:

1. HTTPS is active.
2. `NOVA_ALLOWED_ORIGINS` contains only the real frontend origin.
3. The backend can reach the configured Ollama endpoint.
4. The user database and session database have durable storage and a tested backup/restore procedure.
5. The service remains single-instance/single-worker for V1.
6. Two separate accounts are smoke-tested for data isolation.
7. `npm run lint` and `npm run build` pass in CI.
8. Privacy policy, terms, contact details, and data-retention disclosures are completed with the operator's real legal information.

The repository deliberately does not contain production secrets.
