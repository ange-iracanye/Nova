# Nova V1 Release Checklist

## Code status

- [x] FastAPI production entrypoint
- [x] Durable authentication sessions
- [x] Password hashing and login throttling retained
- [x] Persistent application data directory
- [x] Render persistent disk configuration
- [x] Production CORS configuration
- [x] Security response headers
- [x] Remote Ollama host support
- [x] Backend runtime smoke tests
- [x] Render health check
- [x] SPA fallback configuration

## Required before public traffic

- [ ] Deploy the Render Blueprint successfully.
- [ ] Set `OLLAMA_HOST` to a reachable production Ollama endpoint.
- [ ] Confirm the configured Ollama endpoint contains the configured model.
- [ ] Set `NOVA_ALLOWED_ORIGINS` to the final frontend origin, including the final custom domain if one is used.
- [ ] Set `VITE_API_URL` to the deployed API origin.
- [ ] Confirm `/health` returns HTTP 200.
- [ ] Confirm `/ready` returns HTTP 200 after NovaCore and the LLM are available.
- [ ] Register a new account.
- [ ] Log in and refresh the browser.
- [ ] Verify the session survives an API process restart.
- [ ] Verify chat, streaming chat, conversations, dashboard, settings, quiz, upload, and memory flows.
- [ ] Verify two accounts cannot access one another's data.
- [ ] Verify logout invalidates the session.
- [ ] Verify an unavailable LLM produces a controlled error rather than a server crash.
- [ ] Replace the placeholder privacy/terms operator contact information.

## Launch rule

Nova V1 is public only when every item in **Required before public traffic** is checked. A successful frontend build alone is not a production launch.
