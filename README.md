# Nova AI

Nova is an independent AI tutor built to help students learn through personalized explanations, study tools, and persistent learning context.

> **Project principle:** help students understand the material, not merely receive an answer.

Nova is under active development. This repository is the canonical project: [ange-iracanye/Nova](https://github.com/ange-iracanye/Nova).

## Current implementation

The current deployment configuration defines two Render services:

- **Frontend:** React, Vite, and JavaScript.
- **API:** FastAPI served by Uvicorn.
- **Persistence:** PostgreSQL configured through `NOVA_DATABASE_URL`, with session persistence components in the backend.
- **AI provider:** OpenRouter, configured to use a free model and a free fallback.
- **Local development:** Ollama is supported by the backend configuration.
- **Deployment:** Render configuration is maintained in `render.yaml`.
- **Quality checks:** GitHub Actions covers backend compilation and tests, frontend lint/build checks, and separate security checks.

The repository also contains earlier and experimental modules. A file's presence does not by itself mean that it is part of the deployed request path.

## Repository map

| Path | Purpose |
| --- | --- |
| `backend/` | FastAPI API, tutoring engine, account/session handling, learning systems, memory, retrieval, and provider integration |
| `frontend/` | React/Vite user interface and production build |
| `test/` | Main automated test suite, including release and security tests |
| `backend/test_*.py` | Additional backend-focused tests |
| `datasets/`, `knowledge/`, `Documents/` | Educational and knowledge resources |
| `docs/` | Release, testing, privacy, and operational documentation |
| `scripts/v1_smoke.py` | Live API smoke-test script |
| `.github/workflows/` | CI, security, and maintenance workflows |
| `render.yaml` | Render service configuration |
| `.env.example` | Names and examples of supported environment variables; never put real secrets here |

## Run locally

### 1. Backend

Use Python 3.11, create a virtual environment, and install the project dependencies:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Then install and start the API from the repository root:

```bash
python -m pip install -r requirements.txt
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

The Render service uses `backend.render_entry:app`; the command above is for local development.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Vite normally serves the development UI at `http://localhost:5173`. Configure `VITE_API_URL` for the API address when needed.

### 3. Tests and checks

From the repository root:

```bash
python -m compileall -q backend test
python -m pytest -q
```

For frontend checks:

```bash
cd frontend
npm ci
npm run lint
npm run build
```

The exact outcome depends on your installed environment and configured services. Live-provider, database, and browser checks cannot be proven by a local build alone.

## Production configuration

The checked-in `render.yaml` defines the Render frontend and API services. The API configuration includes:

- Python 3.11.9;
- a single Free instance in Frankfurt;
- a health check at `/health`;
- PostgreSQL and OpenRouter secrets supplied through the hosting dashboard;
- restricted frontend-origin configuration;
- free-model and fallback identifiers.

Never commit real API keys, database connection strings, email credentials, user records, local databases, model weights, or private user data.

See [`docs/V1_RELEASE.md`](docs/V1_RELEASE.md) for the current release checklist and operator tasks.

## Security and release status

A successful GitHub Actions run proves only the checks that ran in that workflow. It does not prove that the live product is safe or ready for public registration.

Before a public launch, verify at minimum:

- live health and readiness endpoints;
- real AI responses and provider quota/fallback behavior;
- persistence across restarts;
- login, logout, and session expiration;
- isolation between two different user accounts;
- account and user-data deletion behavior;
- chat, history, settings, memory, upload, and dashboard flows;
- rate limits, request/upload size limits, and failure handling;
- desktop and mobile browser behavior;
- completed privacy and terms documents, reviewed for the intended jurisdictions.

The current release checklist identifies the privacy and terms pages as templates with operator-specific placeholders. Do not treat them as final legal documents or announce public registration as ready until the required checks and reviews are complete.

The backend also documents a process-level NovaCore lock. Keep the production service single-instance until request isolation is redesigned and verified.

## Cost model

Nova's current deployment target is **€0/month in required paid infrastructure and model API spend**, using free tiers. This is a design target, not a guarantee of unlimited availability. Free services and models can have quotas, cold starts, rate limits, and outages. Nova should fail clearly when a free quota is exhausted rather than silently switching to paid usage.

## Contributing

For changes, keep these principles in mind:

1. Preserve existing behavior unless a change is intentional and tested.
2. Add or update tests for security, account boundaries, and data lifecycle changes.
3. Keep secrets and real user data out of Git.
4. Update documentation when actual implementation or deployment configuration changes.
5. Do not claim a feature is complete solely because a placeholder module or UI exists.

## Project owner

Created and maintained by [Ange Iracanye](https://github.com/ange-iracanye).

Nova is an ongoing learning and engineering project focused on AI tutoring and personalized education.
