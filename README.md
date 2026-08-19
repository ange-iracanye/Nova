# Nova AI

Nova is a student-focused AI tutor with a React frontend and a FastAPI backend.

## Nova V1: $0/month deployment

Nova V1 is configured to run without a paid server, paid persistent disk, or paid model API:

- Render Free for the public backend and static frontend;
- free PostgreSQL persistence through `NOVA_DATABASE_URL` (Supabase Free is supported);
- Gemini Developer API free tier through `GEMINI_API_KEY`;
- local Ollama remains available for development;
- free-tier quotas are treated as hard limits and Nova does not silently upgrade to paid usage.

The Render Free filesystem is ephemeral, so the production runtime restores and periodically synchronizes Nova's generated runtime data to PostgreSQL.

## V1 production hardening

Nova V1 includes:

- salted `scrypt` password hashing for new accounts;
- automatic migration of legacy SHA-256 password hashes after successful login;
- constant-time password comparisons;
- atomic user-database writes;
- fail-closed handling for a corrupted user database;
- persistent production authentication sessions;
- production CORS and security middleware;
- CI checks for Python compilation, authentication security, frontend linting, and production builds;
- explicit FastAPI and Uvicorn runtime dependencies;
- a two-account production smoke-test script.

NovaCore currently relies on a process-level lock and must remain single-instance until request isolation is redesigned.

## Project layout

```text
Nova/
├── backend/        # FastAPI API and Nova engine
├── frontend/       # React + Vite application
├── datasets/       # Educational knowledge data
├── docs/           # Architecture and project documentation
├── test/           # Automated tests
└── requirements.txt
```

## Local development

### Backend

Create and activate a Python virtual environment, install the requirements, then run:

```bash
uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

For local Ollama:

```text
NOVA_LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:3b
```

For the free Gemini provider:

```text
NOVA_LLM_PROVIDER=gemini
NOVA_LLM_MODEL=gemini-3.1-flash-lite
GEMINI_API_KEY=your-key
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite development server normally runs on port `5173`.

## Security notes

- Never commit `.env` files, database URLs, API keys, user databases, model weights, or local memory data.
- Production uses HTTPS and a restricted CORS allowlist.
- Free hosting and AI providers have quotas. Nova must remain usable without a payment method and must fail gracefully when a quota is exhausted.
- Keep the backend single-instance until NovaCore becomes request-isolated.

## Public V1 launch

See [`docs/V1_RELEASE.md`](docs/V1_RELEASE.md) for the exact free deployment and production verification checklist.
