#!/usr/bin/env bash
set -euo pipefail

# Nova's Render build must use only the explicit production requirements.
# Ignore inherited pip configuration/constraints and never require hashes.
unset PIP_CONSTRAINT PIP_REQUIRE_HASHES PIP_CONFIG_FILE PIP_EXTRA_INDEX_URL PIP_INDEX_URL PIP_FIND_LINKS || true

python --version
python -m pip --version

case "$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" in
  3.11) ;;
  *) echo "Nova requires Python 3.11.x on Render."; exit 1 ;;
esac

printf '%s\n' 'Installing Nova production dependencies from requirements-render.txt'
python -m pip --isolated install --upgrade pip --no-cache-dir --disable-pip-version-check --index-url https://pypi.org/simple
python -m pip --isolated install --no-cache-dir --disable-pip-version-check --index-url https://pypi.org/simple --no-input -r ./requirements-render.txt
