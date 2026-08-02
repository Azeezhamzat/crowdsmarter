#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${HOME}/Downloads/crowdsmarter"

if [[ ! -f "${PROJECT_DIR}/docker-compose.yml" ]]; then
  printf 'CrowdSmarter was not found at %s\n' "${PROJECT_DIR}" >&2
  exit 1
fi

read -r -p "CrowdSmarter account email: " EMAIL
read -r -s -p "New password: " PASSWORD
printf '\n'
read -r -s -p "Confirm new password: " CONFIRMATION
printf '\n'

if [[ -z "${EMAIL}" || -z "${PASSWORD}" ]]; then
  printf 'Email and password are required.\n' >&2
  exit 1
fi
if [[ "${PASSWORD}" != "${CONFIRMATION}" ]]; then
  printf 'The passwords do not match.\n' >&2
  exit 1
fi

cd "${PROJECT_DIR}"
printf '%s\n' "${PASSWORD}" | docker compose run --rm -T backend \
  python manage.py reset_local_password --email "${EMAIL}" --activate
printf 'You can now sign in at http://localhost:5173/login\n'
