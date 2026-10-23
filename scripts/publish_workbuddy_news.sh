#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_root"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

lock_dir="$project_root/work/tmp/workbuddy-news-publish.lock"
mkdir -p "$project_root/work/tmp"
if ! mkdir "$lock_dir" 2>/dev/null; then
  echo "Another WorkBuddy news publish is already running."
  exit 0
fi
trap 'rmdir "$lock_dir"' EXIT

python_bin=python3
if [ -x .venv/bin/python ]; then
  python_bin=.venv/bin/python
fi

"$python_bin" scripts/sync_workbuddy_news.py
/usr/bin/git add site/ai-news-daily
if /usr/bin/git diff --cached --quiet; then
  echo "WorkBuddy AI news is already up to date."
  exit 0
fi

stamp="$(TZ=Asia/Shanghai date +%Y-%m-%d)"
/usr/bin/git commit -m "Publish WorkBuddy AI news ${stamp}"
/usr/bin/git push origin main
