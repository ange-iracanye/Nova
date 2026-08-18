# Nova V1 deployment

Nova now has a deployment blueprint for Render in `render.yaml`.

## Services

The blueprint creates:

- `nova-api`: FastAPI/Uvicorn backend
- `nova-frontend`: Vite production static site

## Required production environment variables

### Backend

- `NOVA_ENV=production`
- `NOVA_ALLOWED_ORIGINS=https://<your-frontend-domain>`
- `OLLAMA_HOST=<reachable Ollama endpoint>`

### Frontend

- `VITE_API_URL=https://<your-api-domain>`

## Important V1 architecture constraint

Nova's current LLM layer uses Ollama. The production backend therefore needs an Ollama endpoint that is reachable from the deployed server. A local Ollama process on a developer laptop is not a production dependency.

Nova also currently keeps authentication sessions in process memory and stores the user database as a local JSON file. This is suitable for a controlled single-instance V1 deployment only when the host provides persistent storage and the service remains single-process. Horizontal scaling requires a shared session store and durable database.

## Release gate

Do not mark the service as a fully hardened public release until these are completed in the deployed environment:

1. HTTPS is active.
2. `NOVA_ALLOWED_ORIGINS` contains only the real frontend origin.
3. The backend can reach the configured Ollama endpoint.
4. The user database has durable storage and backups.
5. Authentication uses a secure server-side session mechanism suitable for the deployment topology.
6. Two separate accounts are smoke-tested for data isolation.
7. `npm run lint` and `npm run build` pass in CI.

The repository deliberately does not contain production secrets.
