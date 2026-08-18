# Nova AI

Nova is a student-focused AI tutor with a React frontend and a FastAPI backend.

## V1 production-hardening status

The repository now includes:

- salted `scrypt` password hashing for new accounts;
- automatic migration of legacy SHA-256 password hashes after successful login;
- constant-time password comparisons;
- atomic user-database writes to reduce corruption risk;
- fail-closed handling for a corrupted user database;
- backend authentication regression tests;
- CI checks for Python compilation, authentication security, frontend linting, and production builds;
- explicit FastAPI and Uvicorn runtime dependencies.

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
- The current authentication session store is process-local. For a multi-worker or multi-instance deployment, replace it with a shared session store before scaling horizontally.
- The NovaCore processing lock intentionally protects the current user-switching runtime design. Do not remove it until NovaCore becomes request-isolated.
- Keep the authentication database outside source control and back it up securely.

## Verification

Backend security tests:

```bash
python -m unittest test.test_auth_security -v
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

GitHub Actions runs these checks automatically for pushes to `main` and pull requests targeting `main`.
