#!/usr/bin/env sh
# GitOps-ish sync for n8n workflows. Git is the source of truth by CONVENTION:
# n8n has no reconciler, so nothing stops UI edits drifting — run `export` after
# editing in the UI and commit, run `import` after cloning/rebuilding.
#
#   sh workflows-sync.sh import   # repo -> n8n  (load workflows/*.json into n8n)
#   sh workflows-sync.sh export   # n8n  -> repo (dump all workflows to workflows/)
#   sh workflows-sync.sh diff     # show what export would change (drift check)
set -eu
cd "$(dirname "$0")"
# Git Bash rewrites leading-slash args (/workflows) into Windows paths; disable.
export MSYS_NO_PATHCONV=1

case "${1:-}" in
  import)
    docker compose exec -T n8n n8n import:workflow --separate --input=/workflows
    echo "Imported workflows/ into n8n."
    ;;
  export)
    docker compose exec -T n8n n8n export:workflow --all --separate --output=/workflows
    echo "Exported n8n workflows to workflows/. Review with git diff, then commit."
    ;;
  diff)
    docker compose exec -T n8n sh -c \
      "mkdir -p /tmp/wf && n8n export:workflow --all --separate --output=/tmp/wf >/dev/null 2>&1; diff -rq /tmp/wf /workflows || true"
    ;;
  *)
    echo "usage: sh workflows-sync.sh {import|export|diff}"
    exit 1
    ;;
esac
