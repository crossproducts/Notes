#!/usr/bin/env bash
set -euo pipefail

# Bootstrap Mattermost: create admin, team, bot account, channels
# Run after: docker compose up -d postgres mattermost

MATTERMOST_URL="${MATTERMOST_URL:-http://localhost:8065}"
ADMIN_USER="admin"
ADMIN_PASS="Admin1234!"
ADMIN_EMAIL="admin@local.dev"
BOT_USERNAME="k8s-bot"
BOT_DISPLAY="K8s Bot"
TEAM_NAME="chatops"

echo "Waiting for Mattermost to be ready..."
until curl -sf "$MATTERMOST_URL/api/v4/system/ping" > /dev/null 2>&1; do
  sleep 3
  echo "  still waiting..."
done
echo "Mattermost is ready."

# Create admin user (first user becomes system admin)
echo "Creating admin user..."
curl -sf -X POST "$MATTERMOST_URL/api/v4/users" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$ADMIN_EMAIL\",
    \"username\": \"$ADMIN_USER\",
    \"password\": \"$ADMIN_PASS\"
  }" > /dev/null 2>&1 || echo "  (admin may already exist)"

# Login and get token
echo "Logging in..."
LOGIN_RESPONSE=$(curl -sf -D - -X POST "$MATTERMOST_URL/api/v4/users/login" \
  -H "Content-Type: application/json" \
  -d "{\"login_id\": \"$ADMIN_USER\", \"password\": \"$ADMIN_PASS\"}" 2>/dev/null)

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -i '^token:' | awk '{print $2}' | tr -d '\r\n')
if [ -z "$TOKEN" ]; then
  echo "ERROR: Failed to get auth token. Check admin credentials."
  exit 1
fi

AUTH="Authorization: Bearer $TOKEN"

# Create team
echo "Creating team '$TEAM_NAME'..."
TEAM_ID=$(curl -sf -X POST "$MATTERMOST_URL/api/v4/teams" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"name\": \"$TEAM_NAME\", \"display_name\": \"ChatOps\", \"type\": \"O\"}" \
  2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null) || true

if [ -z "$TEAM_ID" ]; then
  TEAM_ID=$(curl -sf "$MATTERMOST_URL/api/v4/teams/name/$TEAM_NAME" \
    -H "$AUTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
fi
echo "  Team ID: $TEAM_ID"

# Create bot account
echo "Creating bot '$BOT_USERNAME'..."
BOT_RESPONSE=$(curl -sf -X POST "$MATTERMOST_URL/api/v4/bots" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$BOT_USERNAME\",
    \"display_name\": \"$BOT_DISPLAY\",
    \"description\": \"Kubernetes ChatOps bot — @mention me with K8s questions\"
  }" 2>/dev/null) || true

BOT_USER_ID=$(echo "$BOT_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('user_id',''))" 2>/dev/null)

if [ -z "$BOT_USER_ID" ]; then
  # Bot may already exist, find it
  BOT_USER_ID=$(curl -sf "$MATTERMOST_URL/api/v4/bots" \
    -H "$AUTH" | python3 -c "
import sys, json
bots = json.load(sys.stdin)
for b in bots:
    if b['username'] == '$BOT_USERNAME':
        print(b['user_id'])
        break
")
fi
echo "  Bot User ID: $BOT_USER_ID"

# Generate bot token
echo "Generating bot access token..."
BOT_TOKEN=$(curl -sf -X POST "$MATTERMOST_URL/api/v4/users/$BOT_USER_ID/tokens" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"description": "ChatOps bot token"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Add bot to team
curl -sf -X POST "$MATTERMOST_URL/api/v4/teams/$TEAM_ID/members" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"team_id\": \"$TEAM_ID\", \"user_id\": \"$BOT_USER_ID\"}" > /dev/null 2>&1

# Create channels and add bot
for CHANNEL in "general" "k8s-alerts"; do
  echo "Setting up channel '#$CHANNEL'..."
  CHANNEL_ID=$(curl -sf -X POST "$MATTERMOST_URL/api/v4/channels" \
    -H "$AUTH" -H "Content-Type: application/json" \
    -d "{\"team_id\": \"$TEAM_ID\", \"name\": \"$CHANNEL\", \"display_name\": \"$CHANNEL\", \"type\": \"O\"}" \
    2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null) || true

  if [ -z "$CHANNEL_ID" ]; then
    CHANNEL_ID=$(curl -sf "$MATTERMOST_URL/api/v4/teams/$TEAM_ID/channels/name/$CHANNEL" \
      -H "$AUTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
  fi

  curl -sf -X POST "$MATTERMOST_URL/api/v4/channels/$CHANNEL_ID/members" \
    -H "$AUTH" -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$BOT_USER_ID\"}" > /dev/null 2>&1
done

# Add admin to team too
ADMIN_ID=$(echo "$LOGIN_RESPONSE" | tail -1 | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
curl -sf -X POST "$MATTERMOST_URL/api/v4/teams/$TEAM_ID/members" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"team_id\": \"$TEAM_ID\", \"user_id\": \"$ADMIN_ID\"}" > /dev/null 2>&1

echo ""
echo "========================================="
echo "  Setup complete!"
echo "========================================="
echo ""
echo "  Mattermost: http://localhost:8065"
echo "  Admin login: $ADMIN_USER / $ADMIN_PASS"
echo "  Team: $TEAM_NAME"
echo ""
echo "  Add this to your .env file:"
echo "  BOT_TOKEN=$BOT_TOKEN"
echo ""
echo "  Then start the bot:"
echo "  docker compose up -d bot"
echo "========================================="
