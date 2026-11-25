#!/usr/bin/env bash
# Install the dependencies of the backend and the frontend from their lock files.
# Safe to run more than once. Installs nothing that is not in a lock file.
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for tool in uv npm; do
  if ! command -v "$tool" > /dev/null; then
    echo "setup.sh: '$tool' was not found. Install it and run this script again." >&2
    exit 1
  fi
done

echo "== Backend: uv sync --locked"
(cd "$repository_root/backend" && uv sync --locked)

# The Copilot SDK runs a runtime that is not part of its Python package. It
# is downloaded here, ahead of use, into the SDK's cache folder outside the
# repository. The version is the one the pinned SDK names. A second run finds
# it in the cache and downloads nothing new.
echo "== Backend: download the runtime of the Copilot SDK"
(cd "$repository_root/backend" && uv run --no-sync python -m copilot download-runtime --in-process)

# The browser test, the last step of scripts/check.sh, needs a Chromium that
# fits the pinned version of Playwright. A machine that sets
# PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD brings its own browser.
if [[ -n "${PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD:-}" ]]; then
  echo "== Backend: browser for the browser test: skipped, PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD is set"
else
  echo "== Backend: install the browser for the browser test"
  # A failed download does not stop this script. A cloud session runs this
  # script when it starts, and a failing script stops the session from
  # starting; the other checks can still run without a browser.
  if ! (cd "$repository_root/backend" && uv run --no-sync playwright install --only-shell chromium); then
    echo "setup.sh: WARNING: the browser could not be installed." >&2
    echo "setup.sh: WARNING: the browser test in scripts/check.sh will fail until a browser is installed." >&2
  fi
fi

echo "== Frontend: npm ci"
(cd "$repository_root/frontend" && npm ci)

echo "Setup finished."
