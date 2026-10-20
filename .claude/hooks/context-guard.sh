#!/usr/bin/env bash
# UserPromptSubmit: warn Claude when the context window is getting full (value saved by statusline.sh).
DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cat >/dev/null
pct=$(cat "$DIR/.claude/state/context_pct" 2>/dev/null || echo 0)
[[ "$pct" =~ ^[0-9]+$ ]] || exit 0
if [ "$pct" -ge 75 ]; then note="Context is at ${pct}%. Run /handoff now."
elif [ "$pct" -ge 60 ]; then note="Context is at ${pct}%. Finish the current step, then run /handoff; don't start a new step."
else exit 0; fi
jq -n --arg c "$note" '{hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext: $c}}'
