#!/usr/bin/env bash
# install-pipe.sh — idempotent install/update of the Holmes pipe function in Open WebUI.
#
# Auth: signs in as admin@localhost / admin (the default account Open WebUI
# creates when WEBUI_AUTH=false; password is "admin"). The token is held
# only in a shell variable — never written to disk or printed.
#
# How it works:
#   1. Signs in to get a short-lived JWT.
#   2. docker cp's the pipe source into the open-webui container at /tmp/.
#      (Uses `docker cp -` with a tar pipe to work around git-bash path mangling.)
#   3. Uses `docker exec -i python3 -` inside the container to POST the function
#      via localhost:8080. The Python script is piped via stdin to avoid Windows
#      tmp-path issues with docker exec file args.
#   4. Toggles the function active if needed, then verifies the model is listed.
#
# Usage:
#   ./install-pipe.sh            # install or update
#   WEBUI_URL=http://... ./install-pipe.sh   # override external URL (default: localhost:3000)

set -euo pipefail

WEBUI_URL="${WEBUI_URL:-http://localhost:3000}"
CONTAINER="open-webui"
PIPE_ID="holmes"
PIPE_NAME="Holmes (SRE)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPE_FILE="$SCRIPT_DIR/pipe/holmes_pipe.py"

if [[ ! -f "$PIPE_FILE" ]]; then
  echo "ERROR: pipe source not found at $PIPE_FILE" >&2
  exit 1
fi

if ! docker inspect "$CONTAINER" &>/dev/null; then
  echo "ERROR: container '$CONTAINER' is not running. Run: docker compose up -d" >&2
  exit 1
fi

echo "==> Signing in to Open WebUI at $WEBUI_URL ..."
SIGNIN_RESP=$(curl -sf "$WEBUI_URL/api/v1/auths/signin" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@localhost","password":"admin"}')

TOKEN=$(printf '%s' "$SIGNIN_RESP" | docker run --rm -i ghcr.io/jqlang/jq:latest -r '.token // empty')

if [[ -z "$TOKEN" ]]; then
  echo "ERROR: could not obtain admin token. Response:" >&2
  printf '%s\n' "$SIGNIN_RESP" >&2
  exit 1
fi
echo "    token obtained (not printed)"

# Copy the pipe source into the container using tar piped to `docker cp -`.
# This sidesteps git-bash's automatic path conversion for docker cp arguments.
echo "==> Copying pipe source into container ..."
tar -C "$SCRIPT_DIR/pipe" -cf - holmes_pipe.py \
  | docker exec -i "$CONTAINER" bash -c 'tar -xf - -C /tmp && mv /tmp/holmes_pipe.py /tmp/holmes_pipe_install.py'

# Check whether the function already exists.
EXISTING_ID=$(curl -sf \
  -H "Authorization: Bearer $TOKEN" \
  "$WEBUI_URL/api/v1/functions/id/$PIPE_ID" 2>/dev/null \
  | docker run --rm -i ghcr.io/jqlang/jq:latest -r '.id // empty' 2>/dev/null || true)

if [[ "$EXISTING_ID" == "$PIPE_ID" ]]; then
  echo "==> Function '$PIPE_ID' exists — updating ..."
  ENDPOINT="http://localhost:8080/api/v1/functions/id/$PIPE_ID/update"
else
  echo "==> Function '$PIPE_ID' not found — creating ..."
  ENDPOINT="http://localhost:8080/api/v1/functions/create"
fi

# Python script piped via stdin to docker exec to avoid git-bash tmp-path mangling.
INSTALL_PY='
import json, os, urllib.request

with open("/tmp/holmes_pipe_install.py", "r") as f:
    content = f.read()

pipe_id   = os.environ.get("PIPE_ID", "holmes")
pipe_name = os.environ.get("PIPE_NAME", "Holmes (SRE)")
endpoint  = os.environ.get("ENDPOINT", "http://localhost:8080/api/v1/functions/create")
token     = os.environ["WEBUI_TOKEN"]

payload = json.dumps({
    "id": pipe_id,
    "name": pipe_name,
    "content": content,
    "meta": {"description": "Holmes SRE pipe - calls holmes:5050 /api/chat directly"}
}).encode()

req = urllib.request.Request(
    endpoint,
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    },
    method="POST",
)
try:
    with urllib.request.urlopen(req) as resp:
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(json.dumps({"_http_error": e.code, "detail": body}))
'

RESULT=$(printf '%s' "$INSTALL_PY" | docker exec \
  -i \
  -e "WEBUI_TOKEN=$TOKEN" \
  -e "PIPE_ID=$PIPE_ID" \
  -e "PIPE_NAME=$PIPE_NAME" \
  -e "ENDPOINT=$ENDPOINT" \
  "$CONTAINER" python3 -)

RESULT_ID=$(printf '%s' "$RESULT" | docker run --rm -i ghcr.io/jqlang/jq:latest -r '.id // empty')
if [[ "$RESULT_ID" != "$PIPE_ID" ]]; then
  echo "ERROR: create/update did not return expected id '$PIPE_ID'. Response:" >&2
  printf '%s\n' "$RESULT" >&2
  exit 1
fi
echo "    function upserted: id=$RESULT_ID"

# Enable the function if not already active.
IS_ACTIVE=$(printf '%s' "$RESULT" | docker run --rm -i ghcr.io/jqlang/jq:latest -r '.is_active')
if [[ "$IS_ACTIVE" != "true" ]]; then
  echo "==> Enabling function ..."
  TOGGLE=$(curl -sf -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$WEBUI_URL/api/v1/functions/id/$PIPE_ID/toggle")
  IS_ACTIVE=$(printf '%s' "$TOGGLE" | docker run --rm -i ghcr.io/jqlang/jq:latest -r '.is_active')
fi
echo "    is_active=$IS_ACTIVE"

# Verify model appears in the model list.
echo "==> Verifying model in /api/models ..."
MODELS=$(curl -sf -H "Authorization: Bearer $TOKEN" "$WEBUI_URL/api/models")
MODEL_NAME=$(printf '%s' "$MODELS" | docker run --rm -i ghcr.io/jqlang/jq:latest -r \
  --arg mid "$PIPE_ID.$PIPE_ID" '.data[] | select(.id==$mid) | .name' 2>/dev/null || true)

if [[ -n "$MODEL_NAME" ]]; then
  echo "    model visible: id=$PIPE_ID.$PIPE_ID  name=$MODEL_NAME"
else
  echo "WARNING: model '$PIPE_ID.$PIPE_ID' not yet in /api/models" >&2
fi

echo
echo "SUCCESS: Holmes pipe function installed and active."
echo "  Model id : $PIPE_ID.$PIPE_ID"
echo "  UI URL   : $WEBUI_URL"
echo "  Re-run this script after wiping the openwebui-data volume."
