#!/usr/bin/env bash
# purge.sh — delete Open WebUI chats from webui.db inside the open-webui container.
#
# Usage:
#   ./purge.sh --all                   delete every stored chat
#   ./purge.sh --older-than DAYS       delete chats older than N days
#
# Runs via `docker exec` so the stack must be up (docker compose up -d).
# Works from git-bash on Windows.

set -euo pipefail

CONTAINER="open-webui"
DB="/app/backend/data/webui.db"

usage() {
  echo "Usage: $0 --all | --older-than DAYS"
  exit 1
}

if [[ $# -lt 1 ]]; then
  usage
fi

MODE="$1"

case "$MODE" in
  --all)
    echo "Deleting all chats..."
    # Write script into container then execute it (avoids stdin/heredoc issues)
    DELETED=$(docker exec "$CONTAINER" python3 -c "
import sqlite3
db = '${DB}'
con = sqlite3.connect(db)
cur = con.cursor()
cur.execute('SELECT COUNT(*) FROM chat')
before = cur.fetchone()[0]
cur.execute('DELETE FROM chat')
con.commit()
deleted = before
print(deleted)
con.close()
")
    echo "Deleted ${DELETED} chat(s)."
    ;;

  --older-than)
    if [[ $# -lt 2 ]]; then
      echo "Error: --older-than requires a number of days."
      usage
    fi
    DAYS="$2"
    if ! [[ "$DAYS" =~ ^[0-9]+$ ]]; then
      echo "Error: DAYS must be a non-negative integer."
      exit 1
    fi
    echo "Deleting chats older than ${DAYS} day(s)..."
    DELETED=$(docker exec "$CONTAINER" python3 -c "
import sqlite3, time
db = '${DB}'
cutoff = int(time.time()) - (${DAYS} * 86400)
con = sqlite3.connect(db)
cur = con.cursor()
cur.execute('SELECT COUNT(*) FROM chat WHERE updated_at < ?', (cutoff,))
deleted = cur.fetchone()[0]
cur.execute('DELETE FROM chat WHERE updated_at < ?', (cutoff,))
con.commit()
print(deleted)
con.close()
")
    echo "Deleted ${DELETED} chat(s) older than ${DAYS} day(s)."
    ;;

  *)
    usage
    ;;
esac
