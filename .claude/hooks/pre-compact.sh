#!/usr/bin/env bash
# PreCompact: snapshot git state and the next step. Never blocks compaction.
DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
STATE="$DIR/.claude/state"; mkdir -p "$STATE"
cat >/dev/null
ts=$(date '+%Y%m%d-%H%M%S')
{
  echo "# Pre-compaction snapshot $(date '+%Y-%m-%d %H:%M:%S')"
  echo; echo "## Exact next step (STATUS.md)"
  /usr/bin/grep -m1 -A2 'Exact next step' "$DIR/STATUS.md" 2>/dev/null || echo "(not found)"
  echo; echo "## git status --short"; git -C "$DIR" status --short 2>/dev/null
  echo; echo "## git diff --stat"; git -C "$DIR" diff --stat 2>/dev/null
} > "$STATE/precompact-$ts.md"
exit 0
