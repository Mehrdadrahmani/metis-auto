#!/usr/bin/env bash
# SessionStart: inject STATUS.md as context, plus warnings after a compaction or a missed handoff.
DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
STATE="$DIR/.claude/state"; mkdir -p "$STATE"
src=$(jq -r '.source // "startup"')
msg="Project status (from STATUS.md, current facts):"$'\n\n'"$(cat "$DIR/STATUS.md" 2>/dev/null || echo 'STATUS.md is missing.')"
if [ "$src" = "compact" ]; then
  sum=$(ls -t "$STATE"/compact-*.md 2>/dev/null | head -1)
  msg+=$'\n\n'"NOTE: A compaction happened at $(date '+%Y-%m-%d %H:%M'); the summary is in ${sum:-.claude/state/compact-*.md}. Run /handoff before starting new work."
fi
if [ -n "$(git -C "$DIR" status --porcelain 2>/dev/null)" ]; then
  last_commit=$(git -C "$DIR" log -1 --format=%ct 2>/dev/null || echo 0)
  last_handoff=$(stat -f %m "$STATE/last-handoff" 2>/dev/null || echo 0)
  if [ "$last_handoff" -lt "$last_commit" ] || [ ! -f "$STATE/last-handoff" ]; then
    msg+=$'\n\n'"NOTE: The previous session ended without a handoff (uncommitted changes, no handoff since the last commit). Check git status."
  fi
fi
jq -n --arg c "$msg" '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $c}}'
