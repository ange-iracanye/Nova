#!/usr/bin/env bash
set -euo pipefail

# Render can inherit pip configuration/constraints from the build environment.
# Nova intentionally uses a small production dependency file, so remove any
# inherited hash/constraint settings before installing it.
unset PIP_CONSTRAINT PIP_REQUIRE_HASHES PIP_CONFIG_FILE PIP_EXTRA_INDEX_URL || true

python --version
python -m pip --version
printf '%s\n' 'Installing Nova production dependencies from requirements-render.txt'
python -m pip --isolated install --upgrade pip --no-cache-dir --disable-pip-version-check --index-url https://pypi.org/simple
python -m pip --isolated install --no-cache-dir --disable-pip-version-check --index-url https://pypi.org/simple --no-deps -r ./requirements-render.txt

# Install transitive dependencies separately so no inherited requirements/lock
# file can inject unrelated hash-pinned packages into Nova's production build.
python -m pip --isolated install --no-cache-dir --disable-pip-version-check --index-url https://pypi.org/simple -r ./requirements-render.txt
