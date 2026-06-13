#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/ai-cv-review-agent"
BRANCH="main"

cd "$APP_DIR"

git fetch origin "$BRANCH"

current_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse "origin/$BRANCH")"

if [ "$current_sha" = "$remote_sha" ]; then
  echo "Already up to date at $current_sha"
  exit 0
fi

git merge --ff-only "origin/$BRANCH"
docker compose up -d --build
docker image prune -f

echo "Deployed $remote_sha"
