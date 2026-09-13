#!/usr/bin/env bash
set -euo pipefail

# Nova's Render build must not inherit pip policy from the host image.
# In particular, an injected constraints/requirements file can enable
# --require-hashes and make otherwise normal PyPI installs fail.

printf '%s\n' '=== Nova Render pip isolation diagnostics ==='
printf '%s\n' "PWD=$PWD"
printf '%s\n' "Python: $(python --version 2>&1)"
printf '%s\n' "Pip: $(python -m pip --version 2>&1)"

printf '%s\n' '--- pip-related environment before isolation ---'
env | LC_ALL=C sort | grep -E '^(PIP|PYTHON|VIRTUAL_ENV)=' || true

printf '%s\n' '--- pip configuration visible before isolation ---'
python -m pip config debug || true

# Remove all repository-independent pip controls that can enable hash mode,
# constraints, alternate indexes, or cached package content.
unset PIP_CONSTRAINT PIP_REQUIRE_HASHES PIP_CONFIG_FILE PIP_EXTRA_INDEX_URL \
  PIP_INDEX_URL PIP_FIND_LINKS PIP_TRUSTED_HOST PIP_NO_INDEX || true

# Give pip an explicit empty configuration file and explicitly disable hash
# checking. PIP_CONFIG_FILE=/dev/null prevents normal config discovery.
export PIP_CONFIG_FILE=/dev/null
export PIP_REQUIRE_HASHES=0
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

# Also remove known pip caches. The install commands below use --isolated and
# explicit PyPI settings, so neither user nor system pip configuration is used.
rm -rf /root/.cache/pip /opt/render/.cache/pip /opt/render/project/.cache/pip \
  "$HOME/.cache/pip" /tmp/pip-* || true

printf '%s\n' '--- pip configuration after isolation ---'
env | LC_ALL=C sort | grep -E '^(PIP|PYTHON|VIRTUAL_ENV)=' || true
python -m pip config debug || true

case "$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" in
  3.11) ;;
  *) echo "Nova requires Python 3.11.x on Render."; exit 1 ;;
esac

printf '%s\n' '=== Installing Nova production dependencies ==='
printf '%s\n' 'requirements-render.txt is the only repository dependency input.'

# --isolated ignores all user/environment configuration except variables
# explicitly supplied by the command. The explicit index and no-cache flags
# make the source and cache behavior deterministic.
python -m pip --isolated install --upgrade pip \
  --no-cache-dir \
  --disable-pip-version-check \
  --index-url https://pypi.org/simple \
  --no-input

python -m pip --isolated install \
  --no-cache-dir \
  --disable-pip-version-check \
  --index-url https://pypi.org/simple \
  --no-input \
  --require-hashes=false \
  --force-reinstall \
  -r ./requirements-render.txt

printf '%s\n' '=== Verifying Nova production dependency consistency ==='
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
