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

echo "== Frontend: npm ci"
(cd "$repository_root/frontend" && npm ci)

echo "Setup finished."
