#!/usr/bin/env bash
set -euo pipefail

# Nova's Render build is deliberately isolated from any inherited pip state.
# This prevents stale/corrupted wheels, constraints, hash policies, and custom
# indexes from changing the production dependency resolution.
rm -rf /root/.cache/pip /opt/render/.cache/pip /opt/render/project/.cache/pip ~/.cache/pip /tmp/pip-* || true
unset PIP_CONSTRAINT PIP_REQUIRE_HASHES PIP_CONFIG_FILE PIP_EXTRA_INDEX_URL PIP_INDEX_URL PIP_FIND_LINKS || true
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

python --version
python -m pip --version

case "$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" in
  3.11) ;;
  *) echo "Nova requires Python 3.11.x on Render."; exit 1 ;;
esac

printf '%s\n' 'Installing Nova production dependencies from requirements-render.txt'
python -m pip --isolated install --upgrade pip --no-cache-dir --disable-pip-version-check --index-url https://pypi.org/simple
python -m pip --isolated install --no-cache-dir --disable-pip-version-check --index-url https://pypi.org/simple --no-input --force-reinstall -r ./requirements-render.txt

printf '%s\n' 'Verifying Nova production dependency consistency'
python -m pip --isolated check
python - <<'PY'
import fastapi
import flask
import psycopg
import uvicorn

print("Nova dependency verification passed")
print(f"FastAPI {fastapi.__version__}")
print(f"Flask {flask.__version__}")
print(f"psycopg {psycopg.__version__}")
print(f"Uvicorn {uvicorn.__version__}")
PY
