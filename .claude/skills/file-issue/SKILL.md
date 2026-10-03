---
name: file-issue
description: File a new GitHub issue in wmeints/tankgame for a bug or an enhancement. Use when the user asks to file, open, log, report or create an issue, bug report, feature request or enhancement, or says "make a ticket for this" about something in the tank game.
argument-hint: "[bug|enhancement] <short description>"
allowed-tools: Bash(gh issue list*), Bash(gh issue view*), Bash(gh label list*), Bash(git log*), Bash(git rev-parse*), Read, Grep, Glob
---

# File an issue

Files one issue in `wmeints/tankgame` with the `gh` CLI. Input: `$ARGUMENTS` (may be empty, then use the conversation for context).

## 1. Classify

Decide whether it is a **bug** (something behaves wrong, crashes, or differs from the original Roblox "Tank Game!" / Diep.io values) or an **enhancement** (new tank, feature, balance change, UX/tooling improvement). If the user said which, use that. If it is genuinely unclear, ask once.

Labels: `bug` or `enhancement`. Add an extra existing label only when it clearly fits (`documentation`, `accessibility`, `good first issue`). Never create new labels.

## 2. Gather context

Do just enough research to make the issue actionable. Don't fix anything.

- Find the code involved and cite it as repo-relative `path:line` (e.g. `src/tankgame/world.py:212`). Use the CLAUDE.md architecture map: simulation in `world.py`, entities in `entities/`, balance in `data/tanks.py` and `data/progression.py`, bot behavior and difficulty in `ai.py`, scenes and rendering in `scenes/`, `render.py`, `hud.py`, save data in `save.py` and `meta.py`.
- For bugs, get the current commit with `git rev-parse --short HEAD`. If the conversation has an error, traceback, failing test or `--simulate` output, include the relevant part verbatim (trimmed).
- Don't launch the interactive game to reproduce. `uv run pytest` or `SDL_VIDEODRIVER=dummy uv run tankgame --simulate N` are fine if a repro is quick.
- Check for duplicates: `gh issue list --state all --search "<keywords>" --limit 10`. If one looks like the same issue, show it to the user and ask whether to still file, or comment there instead.

Don't invent details. Leave out sections you have nothing real for, and mark guesses as guesses.

## 3. Draft

Title: imperative or descriptive, under ~70 characters, no `[Bug]` prefix (the label covers that). E.g. "Lasers ignore shape collisions past the arena edge", "Add Hybrid evolution from Destroyer".

Bug body:

```markdown
## Summary
<one or two sentences>

## Steps to reproduce
1. ...

## Expected behavior
...

## Actual behavior
... (include trimmed traceback/output in a code block)

## Where to look
- `src/tankgame/...:line`: why it's relevant

## Environment
Commit `<sha>`, Python 3.14, pygame-ce
```

Enhancement body:

```markdown
## Summary
<what and why, one paragraph>

## Proposal
- ...

## Acceptance criteria
- [ ] ...
- [ ] `uv run pytest` and `--simulate 3000` pass

## Where to look
- `src/tankgame/...:line`: why it's relevant
```

For balance or tank-tree changes, note the reference values from the original game/Diep.io if known, and mention `tests/test_tanks.py` when the evolution tree changes.

## 4. Confirm, then file

Creating an issue is public. Show the user the title, labels and full body, and ask for approval before filing. Apply any edits they request.

On approval, write the body to a file in the scratchpad directory (avoids shell-quoting problems) and run:

```bash
gh issue create --repo wmeints/tankgame --title "<title>" --label <label> --body-file <path>
```

Reply with the issue URL `gh` prints. If `gh` fails (not authenticated, network), show the error and suggest `! gh auth login`; don't retry in a loop.
