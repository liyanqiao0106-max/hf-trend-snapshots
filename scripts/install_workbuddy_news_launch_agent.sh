#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")/.." && pwd)"
label="com.liyanqiao.workbuddy-news-publish"
source_plist="$project_root/scripts/${label}.plist"
target_plist="$HOME/Library/LaunchAgents/${label}.plist"
domain="gui/$(id -u)"

mkdir -p "$project_root/work/logs" "$HOME/Library/LaunchAgents"
/usr/bin/plutil -lint "$source_plist"
/usr/bin/install -m 0644 "$source_plist" "$target_plist"
/bin/launchctl bootout "$domain/$label" 2>/dev/null || true
/bin/launchctl bootstrap "$domain" "$target_plist"
/bin/launchctl enable "$domain/$label"

echo "Installed $label from $target_plist"
/bin/launchctl print "$domain/$label" | /usr/bin/sed -n '1,80p'
