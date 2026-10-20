#!/usr/bin/env bash
# Status line: [model] ctx N% · 5h N% · WP-xx. Also saves the context % for context-guard.sh.
DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
STATE="$DIR/.claude/state"; mkdir -p "$STATE"
in="$(cat)"
model=$(jq -r '.model.display_name // "?"' <<<"$in")
ctx=$(jq -r '.context_window.used_percentage // empty | floor' <<<"$in" 2>/dev/null)
five=$(jq -r '.rate_limits.five_hour.used_percentage // empty | floor' <<<"$in" 2>/dev/null)
wp=$(/usr/bin/grep -m1 -oE 'Current WP: \**WP-[0-9]+[a-z]?' "$DIR/STATUS.md" 2>/dev/null | /usr/bin/grep -oE 'WP-[0-9]+[a-z]?')
[ -n "$ctx" ] && echo "$ctx" > "$STATE/context_pct"
color() {  # $1 = value, $2 = yellow from, $3 = red from
  local v=$1
  if [ -z "$v" ]; then printf '?'; elif [ "$v" -ge "$3" ]; then printf '\033[31m%s%%\033[0m' "$v"
  elif [ "$v" -ge "$2" ]; then printf '\033[33m%s%%\033[0m' "$v"; else printf '\033[32m%s%%\033[0m' "$v"; fi
}
printf '[%s] ctx %s · 5h %s · %s\n' "$model" "$(color "$ctx" 50 60)" "$(color "$five" 75 90)" "${wp:-WP-?}"
