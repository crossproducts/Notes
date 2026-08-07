#!/usr/bin/env bash
# Ask HolmesGPT a question via the HTTP API.
# Usage: ./ask.sh "why is payment-api restarting?"
set -euo pipefail

QUESTION="${1:?usage: ./ask.sh \"your question\"}"

curl -s http://localhost:5050/api/chat \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg q "$QUESTION" '{ask: $q}')" \
  | jq -r '.analysis // .'
