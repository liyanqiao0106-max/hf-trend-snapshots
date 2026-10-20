#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_root"

python_bin=python3
if [ -x .venv/bin/python ]; then
  python_bin=.venv/bin/python
fi

"$python_bin" scripts/sync_workbuddy_news.py
git add site/ai-news-daily
if git diff --cached --quiet; then
  echo "WorkBuddy AI news is already up to date."
  exit 0
fi

stamp="$(TZ=Asia/Shanghai date +%Y-%m-%d)"
git commit -m "Publish WorkBuddy AI news ${stamp}"
git push origin main
