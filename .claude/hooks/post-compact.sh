#!/usr/bin/env bash
# PostCompact: save the compaction summary and flag that a handoff is needed.
DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
STATE="$DIR/.claude/state"; mkdir -p "$STATE"
ts=$(date '+%Y%m%d-%H%M%S')
jq -r '.compact_summary // "(no compact_summary in hook input)"' > "$STATE/compact-$ts.md"
touch "$STATE/needs-handoff"
exit 0
