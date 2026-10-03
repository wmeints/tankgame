#!/usr/bin/env bash
# PreToolUse(Bash): block commands that would launch the interactive game
# (opens a window, blocks the agent, and writes the real save file).
cmd=$(jq -r '.tool_input.command // ""')

# Match tankgame only in command position: start of a (sub)command, after
# optional VAR=value assignments, run directly or via uv/python.
launch='(^|[;&|(]|&&|\|\|)[[:space:]]*([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*((uv run[[:space:]]+)?(python3?[[:space:]]+-m[[:space:]]+)?tankgame|python3?[[:space:]]+-m[[:space:]]+tankgame)([[:space:]]|$)'
if grep -Eq "$launch" <<<"$cmd" \
   && ! grep -q -- '--simulate' <<<"$cmd"; then
  echo "Blocked: the interactive game opens a window and writes the real save file. Use 'SDL_VIDEODRIVER=dummy uv run tankgame --simulate 3000' to verify, or ask the user to play-test." >&2
  exit 2
fi
exit 0
