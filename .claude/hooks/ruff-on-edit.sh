#!/usr/bin/env bash
# PostToolUse(Edit|Write): format the edited Python file with ruff, apply safe
# lint fixes, then report anything left (including syntax errors and
# complexity violations) back to Claude.
f=$(jq -r '.tool_response.filePath // .tool_input.file_path // ""')
[[ "$f" == *.py && -f "$f" ]] || exit 0
cd "$CLAUDE_PROJECT_DIR" || exit 0

uv run --quiet ruff format --quiet "$f" >/dev/null 2>&1
uv run --quiet ruff check --quiet --fix "$f" >/dev/null 2>&1
if ! out=$(uv run --quiet ruff check --output-format concise "$f" 2>&1); then
  echo "ruff found problems in $f (it was auto-formatted; safe fixes were applied):" >&2
  echo "$out" >&2
  echo "Fix these. For complexity rules (C901, PLR09xx), split the function into smaller helpers instead of adding noqa." >&2
  exit 2
fi
exit 0
