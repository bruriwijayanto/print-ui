#!/usr/bin/env bash
set -euo pipefail

BACKEND_PORT="${BACKEND_PORT:-8000}"
URL="http://localhost:${BACKEND_PORT}/api/health"

response="$(curl -sS -w '\n%{http_code}' "$URL")"
body="$(echo "$response" | head -n -1)"
code="$(echo "$response" | tail -n1)"

echo "$body"

if [ "$code" != "200" ]; then
  echo "Health check failed with HTTP $code" >&2
  exit 1
fi
