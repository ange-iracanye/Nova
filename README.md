# Nova AI

Nova is a student-focused AI tutor with a React frontend and a FastAPI backend.

## V1 production status

Nova V1 includes:

- salted `scrypt` password hashing for new accounts;
- automatic migration of legacy SHA-256 password hashes after successful login;
- constant-time password comparisons;
- atomic user-database writes to reduce corruption risk;
- fail-closed handling for a corrupted user database;
- persistent SQLite-backed authentication sessions;
- production CORS and security middleware;
- CI checks for Python compilation, authentication security, frontend linting, and production builds;
- explicit FastAPI and Uvicorn runtime dependencies;
- a two-account production smoke-test script.

The production Render configuration uses a persistent 10 GB application disk and a single backend instance. NovaCore currently relies on a process-level lock and must remain single-instance until request isolation is redesigned.

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

The API exposes health/status endpoints and, in development, FastAPI documentation.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite development server normally runs on port `5173`.

## Security notes

- Do not commit `.env` files, user databases, model weights, tokens, or local memory data.
- Production deployments should use HTTPS and a restricted CORS allowlist rather than broad origins.
- The production authentication/session database must remain on persistent storage and be backed up securely.
- The production backend is intentionally single-instance because NovaCore currently uses a process-level lock around its user-switching runtime design. Do not scale horizontally until NovaCore becomes request-isolated.
- Review third-party model/data processing and the final privacy/terms documents before accepting public users.

## Verification

Backend security tests:

```bash
python -m unittest test.test_auth_security -v
```

V1 release tests:

```bash
python -m unittest test.v1.test_release -v
python -m pytest test/v1/test_production_security.py -q
```

Frontend checks:

```bash
cd frontend
npm install
npm run lint
npm run build
```

Production smoke test:

```text
set NOVA_SMOKE_URL=https://your-api.example.com
set NOVA_SMOKE_EMAIL_A=test-a@example.com
set NOVA_SMOKE_PASSWORD_A=...
set NOVA_SMOKE_EMAIL_B=test-b@example.com
set NOVA_SMOKE_PASSWORD_B=...
python scripts/v1_smoke.py
```

GitHub Actions runs the repository's automated checks for pushes to `main` and pull requests targeting `main`.

## Public V1 launch gate

The repository is deployment-ready, but Nova should not be advertised as publicly launched until the live deployment has passed the V1 smoke test, persistence/restart test, AI-provider test, and legal/privacy review. See `docs/V1_RELEASE.md`.
