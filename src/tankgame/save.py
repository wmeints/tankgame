"""Profile persistence (gems, caps, unlocks, quests...)."""

import copy
import json
import os
from pathlib import Path

from .data import progression as P

SAVE_VERSION = 1


def default_save_path() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "tankgame" / "save.json"


DEFAULT_PROFILE = {
    "version": SAVE_VERSION,
    "gems": P.STARTING_GEMS,
    "caps": dict.fromkeys(P.STATS, 0),  # cap upgrades bought per stat
    "unlocked_tanks": [],  # shop / quest / wheel tanks
    "skins": ["Classic"],
    "skin": "Classic",
    "difficulty": "normal",
    "total_score": 0,  # rank XP
    "total_kills": 0,
    "best_score": 0,
    "best_level": 1,
    "rebirths": 0,
    "pending_xp": 0,  # head start for next run
    "spins": 0,
    "last_free_spin": "",
    "redeemed_codes": [],
    "shape_counts": {"square": 0, "triangle": 0, "pentagon": 0, "alpha": 0, "shiny": 0},
    "quests": {"daily_date": "", "daily": [], "weekly_id": "", "weekly": [], "unique": {}},
}


def migrate(data: dict) -> dict:
    """Fill in missing keys so older saves keep working."""
    prof = copy.deepcopy(DEFAULT_PROFILE)
    for key, val in data.items():
        if isinstance(val, dict) and isinstance(prof.get(key), dict):
            prof[key].update(val)
        else:
            prof[key] = val
    prof["version"] = SAVE_VERSION
    return prof


def load(path: Path | None = None) -> dict:
    path = path or default_save_path()
    try:
        with open(path) as f:
            return migrate(json.load(f))
    except OSError, ValueError:
        return copy.deepcopy(DEFAULT_PROFILE)


def save(profile: dict, path: Path | None = None) -> None:
    path = path or default_save_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(profile, f, indent=1)
    tmp.replace(path)
