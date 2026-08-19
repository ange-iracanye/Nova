# Nova V1 testing

Nova contains an older prototype/training tree that is intentionally kept for reference. Some files under `test/` exercise that pre-V1 architecture and are not the production release contract.

The repository's default `pytest` command is therefore the focused V1 suite:

```bash
python -m pytest -q
```

The release suite covers authentication, persistent sessions, dynamic subjects, evidence-based dashboard aggregation, and production security defaults. The CI workflow runs the same default suite.

Legacy prototype tests remain available under `test/` for future cleanup or archival work, but they are not a V1 release gate.

## Live production smoke test

For a deployed API, use `scripts/v1_smoke.py` with two already-created test accounts. It verifies:

- HTTPS API reachability;
- health endpoint;
- login/session identity for both users;
- authenticated dashboard access;
- cross-account dashboard authorization (A cannot request B's dashboard);
- logout revocation.

Windows CMD example:

```bat
set NOVA_SMOKE_URL=https://your-api-domain.example
set NOVA_SMOKE_EMAIL_A=test-a@example.com
set NOVA_SMOKE_PASSWORD_A=your-test-password
set NOVA_SMOKE_EMAIL_B=test-b@example.com
set NOVA_SMOKE_PASSWORD_B=your-test-password
python scripts\v1_smoke.py
```

The script never prints passwords or session tokens and does not create accounts.

For a real deployment, also perform browser smoke tests because no repository test can prove that the deployed frontend, DNS, cookies, CORS, Render environment variables, Ollama endpoint, responsive UI, and real user experience are correct in the live environment.
