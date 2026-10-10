#!/usr/bin/env bash
# Local Mac entrypoint. Keep temporary files and tool caches inside this project.
set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_root"

mkdir -p work/tmp work/cache
export TMPDIR="$project_root/work/tmp"
export TMP="$project_root/work/tmp"
export TEMP="$project_root/work/tmp"
export PIP_CACHE_DIR="$project_root/work/cache/pip"
export npm_config_cache="$project_root/work/cache/npm"
export HF_HOME="$project_root/work/cache/huggingface"
export XDG_CACHE_HOME="$project_root/work/cache"
export PLAYWRIGHT_BROWSERS_PATH="$project_root/work/cache/playwright"
export PYTHONDONTWRITEBYTECODE=1

python_bin=python3
if [ -x .venv/bin/python ]; then
  python_bin=.venv/bin/python
fi

case "${1:-serve}" in
  serve) "$python_bin" -m http.server 8000 --directory site ;;
  test) "$python_bin" -m unittest discover -s tests -v ;;
  collect) "$python_bin" -m dashboard.run_daily --scope all ;;
  collect-x) shift; "$python_bin" -m dashboard.x_watch "$@" ;;
  package) "$python_bin" scripts/build_mac_package.py --output "$project_root/AI产业看板_Mac迁移完整包_最新.zip" ;;
  *)
    echo 'Usage: bash scripts/run-local.sh [serve|test|collect|collect-x [--days N] [--per-account N] [--retry-failed]|package]' >&2
    exit 2
    ;;
esac
