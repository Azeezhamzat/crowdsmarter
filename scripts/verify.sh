#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."

(
  cd backend
  python -m pip install -e '.[dev]'
  python manage.py makemigrations --check --dry-run
  ruff check .
  ruff format --check .
  mypy crowdsmarter apps
  pytest --cov=apps --cov-report=term-missing --cov-fail-under=85
)

(
  cd frontend
  npm install
  npm run lint
  npm run typecheck
  npm test -- --run
  npm run build
)
