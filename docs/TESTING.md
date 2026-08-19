# Nova V1 testing

Nova contains an older prototype/training tree that is intentionally kept for reference. Some files under `test/` exercise that pre-V1 architecture and are not the production release contract.

The repository's default `pytest` command is therefore the focused V1 suite:

```bash
python -m pytest -q
```

The release suite covers authentication, persistent sessions, dynamic subjects, and evidence-based dashboard aggregation. The CI workflow runs the same default suite.

Legacy prototype tests remain available under `test/` for future cleanup or archival work, but they are not a V1 release gate.

For a real deployment, also perform the manual production smoke tests in `docs/V1_PUBLIC_LAUNCH.md` because no repository test can prove that the deployed Ollama endpoint, Render environment variables, DNS, cookies, CORS, and two-user isolation are correct in the live environment.
