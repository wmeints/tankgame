#!/usr/bin/env bash
# Stop: if Python code changed since HEAD, run the unit tests and the headless
# smoke test. On failure, send Claude back to fix it (once per stop attempt).
input=$(cat)
cd "$CLAUDE_PROJECT_DIR" || exit 0

changed=$( { git diff --name-only HEAD; git ls-files --others --exclude-standard; } 2>/dev/null \
  | grep -E '\.py$|^pyproject\.toml$|^uv\.lock$' )
[[ -n "$changed" ]] || exit 0

export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy
fail=""
if ! out=$(uv run --quiet pytest -q -x 2>&1); then
  fail+=$'pytest failed:\n'"$(tail -n 40 <<<"$out")"$'\n'
fi
if ! out=$(timeout 120 uv run --quiet tankgame --simulate 3000 2>&1); then
  fail+=$'smoke test (tankgame --simulate 3000) failed:\n'"$(tail -n 40 <<<"$out")"$'\n'
fi
[[ -z "$fail" ]] && exit 0

if [[ "$(jq -r '.stop_hook_active // false' <<<"$input")" == "true" ]]; then
  # Already sent back once; don't loop forever, but tell the user.
  jq -n --arg m "Verification still failing after a fix attempt. Run 'uv run pytest' to see details." '{systemMessage: $m}'
  exit 0
fi
echo "$fail" >&2
exit 2
