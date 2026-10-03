# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An offline clone of the Roblox "Tank Game!" (a Diep.io-style arena shooter), written in Python 3.14 with pygame-ce. The player fights 12 AI bots. Tank names, evolution levels and build paths follow the original game. Damage and XP numbers follow Diep.io's values, scaled up to 150 levels.

## Commands

Tooling is managed by mise (installs uv) and uv:

```bash
mise install && uv sync                                  # one-time setup
uv run tankgame                                          # play
uv run pytest                                            # all tests
uv run pytest tests/test_tanks.py::test_every_tank_can_fire   # single test
SDL_VIDEODRIVER=dummy uv run tankgame --simulate 3000    # headless smoke test
uv run ruff format . && uv run ruff check --fix .        # format + lint
```

Ruff is configured in `pyproject.toml` with complexity limits (McCabe 10, max 12 branches, 40 statements, 6 args). When a function exceeds them, split it into smaller helpers. Don't add `noqa`. The existing `# noqa: C901, PLR09xx` markers are a baseline of functions waiting to be refactored. Unused imports and variables are reported but never auto-removed (`unfixable`), because they're often unused only until the next edit. `data/tanks.py` is hand-aligned and excluded from the formatter only.

`--simulate N` draws every menu scene and shop tab once, then autoplays arena runs for N frames with rendering. It exits non-zero if no bot evolved. Run it after changing rendering, scenes or the simulation. Unit tests don't cover those.

`tests/conftest.py` sets the SDL video and audio drivers to `dummy`, so tests that build a `World` run headless.

## Architecture

**Game loop & scenes** (`game.py`, `scenes/`): `Game` runs a fixed-timestep loop (`config.DT` = 1/60 s). Each frame it calls `scene.handle_event`, `scene.update(dt)` and `scene.draw(surf)` on the current scene. `game.goto(scene)` switches scenes. Every scene subclasses `scenes.Scene`, and menu sub-screens subclass `BackScene` (in `scenes/menu.py`). Scene modules are imported lazily inside functions to avoid circular imports.

**Simulation vs. rendering**: `world.World` owns the whole arena simulation: tanks, shapes, bullets, beams, collisions, kills, XP and gem rewards, and quest events. It has no rendering code, so it runs headless for tests and `--simulate`. `scenes/arena.py` (`ArenaScene`) wraps a `World` and does input, camera and drawing through `render.py` and `hud.py`. `spatial.Grid` is a spatial hash. `World` uses one grid for solids and one for bullets.

**Entities** (`entities/`): `Tank` is used for both the player and the bots. Bots get a `Brain` (`ai.py`) that sets the tank's movement, aim and `firing` inputs, spends stat points and picks evolutions. Autoplay gives the player a `Brain` in the same way. Each frame a tank fires the barrels from its tank definition. `barrel["kind"]` selects the behavior: `bullet`, `spike`, `rocket`, `laser`, `freeze` or `flame`. Lasers go through `World.fire_laser` instead of spawning a `Bullet`. Tanks call back into the arena (`tank.arena`) for kills, XP, and spawning bullets.

**Data-driven balance** (`data/`):
- `data/tanks.py`: the full evolution tree, built at import time with `T(...)` calls into the `TANKS` dict. Barrels are built with `B(...)` and the `fan`/`ring` helpers. The module docstring documents every barrel field. `parents` can contain `ANY` ("*"), which means any tank of level 15 or higher. `evolution_options()` holds the tree-walking rules (lock checks happen elsewhere). `price` and `unlock` mark tanks that must be bought or unlocked first.
- `data/progression.py`: XP curve, stat formulas, shapes, gems, ranks, quests, codes, wheel prizes and skins.
- `ai.py` `DIFFICULTY`: difficulty settings for the bots, plus the player damage multiplier (`hurt`).

**Persistent meta-progression** (`save.py`, `meta.py`): the profile is a plain dict persisted as JSON at `$XDG_DATA_HOME/tankgame/save.json` (default `~/.local/share/...`). `meta.py` has functions that mutate the profile: quests, code redemption, the prize wheel, stat caps, ranks and unlocks. When you add a profile field, add it to `save.DEFAULT_PROFILE`. `migrate()` merges old saves into the defaults, one dict level deep. `Game.save()` does nothing in headless mode. Tests and `--simulate` use a `deepcopy` of `DEFAULT_PROFILE`, never the real save.

**Misc**: `sfx.py` synthesizes all sounds at runtime, so there are no asset files. Headless mode swaps in `_NoSfx`. `config.py` holds the screen and arena constants and the Diep-style color palette.

## Tests

`tests/test_tanks.py` checks invariants of the evolution tree: every parent exists and has a lower level, every tank is reachable from Basic, the original game's evolution levels and prices hold, and every tank can fire inside a real `World`. Run it after editing `data/tanks.py`.

## Agent harness (`.claude/`)

`.claude/settings.json` sets up the following guardrails:
- **Stop hook** (`verify-on-stop.sh`): if any `.py`, `pyproject.toml` or `uv.lock` file differs from HEAD, it runs `ruff check`, `ruff format --check`, `pytest` and `--simulate 3000` before the turn ends. If either fails, it sends you back to fix it, once per stop attempt.
- **PreToolUse(Bash)** (`guard-bash.sh`): blocks launching the interactive game. The game opens a window, blocks the session, and writes the real save file. Verify with `--simulate` instead, or ask the user to play-test.
- **PostToolUse(Edit|Write)** (`ruff-on-edit.sh`): runs `ruff format` and `ruff check --fix` on every Python file you edit, then sends back any remaining violations (including syntax errors and complexity limits) for you to fix.
- **Permissions**: edits under `src/` and `tests/` plus test, simulate and local git commands are allowed. Dependency and `.claude/` changes need approval. `git push`, `git reset --hard`, `git clean`, `rm -rf` and writes to the real save directory are denied.
