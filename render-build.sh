#!/usr/bin/env bash
set -euo pipefail

# Nova's Render build must use only the explicit production requirements.
# Purge every known pip cache location first so Render cannot reuse a corrupted
# wheel from an older build. Also ignore inherited pip configuration/constraints.
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
