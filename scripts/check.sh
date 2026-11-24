#!/usr/bin/env bash
# Run every automatic check of the project. This is the one command to run.
# It stops at the first failure. It installs nothing: run scripts/setup.sh first.
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
backend="$repository_root/backend"
frontend="$repository_root/frontend"

if [[ ! -d "$backend/.venv" || ! -d "$frontend/node_modules" ]]; then
  echo "check.sh: dependencies are not installed. Run scripts/setup.sh first." >&2
  exit 1
fi

current_step=""
report_failure() {
  echo "check.sh: FAILED at step: $current_step" >&2
}
trap report_failure ERR

step() {
  current_step="$1"
  echo
  echo "== $current_step"
}

step "Document map"
python3 "$repository_root/scripts/check_document_map.py"

step "Architecture file paths"
python3 "$repository_root/scripts/check_architecture.py"

# The Python tools run from the repository root and read their settings from
# backend/pyproject.toml, so backend/ and scripts/ follow one set of rules.
# "--no-sync" stops uv from installing anything here.
cd "$repository_root"
python_tool=(uv run --no-sync --project "$backend")
python_config="$backend/pyproject.toml"

step "Python: ruff lint (backend and scripts)"
"${python_tool[@]}" ruff check --config "$python_config" backend scripts

step "Python: ruff format check (backend and scripts)"
"${python_tool[@]}" ruff format --check --config "$python_config" backend scripts

step "Python: mypy (backend and scripts)"
"${python_tool[@]}" mypy --config-file "$python_config" backend scripts

step "Python: pytest (backend and scripts)"
(cd "$backend" && uv run --no-sync pytest)

cd "$frontend"

step "Frontend: ESLint"
npm run --silent lint

step "Frontend: type check"
npm run --silent typecheck

step "Frontend: Vitest"
npm run --silent test

trap - ERR
echo
echo "All checks passed."
