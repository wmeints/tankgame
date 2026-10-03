#!/usr/bin/env bash
# PostToolUse(Edit|Write): fast syntax check on edited Python files.
f=$(jq -r '.tool_response.filePath // .tool_input.file_path // ""')
[[ "$f" == *.py && -f "$f" ]] || exit 0
if ! out=$(cd "$CLAUDE_PROJECT_DIR" && uv run --quiet python -m py_compile "$f" 2>&1); then
  echo "Syntax error in $f:" >&2
  echo "$out" >&2
  exit 2
fi
exit 0
