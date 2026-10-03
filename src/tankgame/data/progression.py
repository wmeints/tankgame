"""Levels, XP, stats, shapes, gems, ranks and quests.

Numbers the original Roblox game publishes (stat names, max caps, evolution
levels, rebirth at 150, Railgun price) are copied. Numbers it does not publish
(XP curve, per-point effects, shape values) are based on Diep.io, which the
original clones, and scaled up to a 150 level cap.
"""

MAX_LEVEL = 150
REBIRTH_LEVEL = 150


def xp_to_next(level: int) -> int:
    """XP needed to go from `level` to `level + 1`."""
    return round(4 * level**1.6 + 10)


_TOTAL_XP = [0, 0]  # index = level, value = total score needed to reach it
for _lvl in range(1, MAX_LEVEL):
    _TOTAL_XP.append(_TOTAL_XP[-1] + xp_to_next(_lvl))


def total_xp_for_level(level: int) -> int:
    return _TOTAL_XP[max(1, min(level, MAX_LEVEL))]


def level_for_xp(xp: float) -> int:
    level = 1
    while level < MAX_LEVEL and xp >= _TOTAL_XP[level + 1]:
        level += 1
    return level


def stat_points_for_level(level: int) -> int:
    """Total stat points earned when reaching `level`.

    One point per level up to 45, then one point every 3 levels (Diep style).
    """
    pts = max(0, min(level, 45) - 1)
    if level >= 48:
        pts += (level - 45) // 3
    return pts


# --- Stats -----------------------------------------------------------------

STATS = ["dmg", "bspd", "reload", "bhp", "maxhp", "regen", "speed", "body"]
STAT_NAMES = {
    "dmg": "Damage",
    "bspd": "Bullet Speed",
    "reload": "Fire Rate",
    "bhp": "Bullet Health",
    "maxhp": "Max Health",
    "regen": "Health Regen",
    "speed": "Tank Speed",
    "body": "Body Damage",
}
STAT_COLORS = {
    "dmg": (230, 100, 100),
    "bspd": (100, 160, 240),
    "reload": (240, 200, 90),
    "bhp": (180, 120, 240),
    "maxhp": (240, 110, 200),
    "regen": (240, 160, 110),
    "speed": (110, 230, 230),
    "body": (150, 240, 110),
}
BASE_CAP = 7
# Highest caps reachable by buying upgrades (from the original game's wiki).
MAX_CAPS = {
    "dmg": 12,
    "bspd": 13,
    "reload": 12,
    "bhp": 11,
    "maxhp": 12,
    "regen": 11,
    "speed": 13,
    "body": 12,
}


def cap_upgrade_cost(n: int) -> int:
    """Gem cost of the n-th (1-based) cap upgrade for one stat."""
    return 2500 * 2 ** (n - 1)


def bullet_damage(p_dmg: int, p_bhp: int) -> float:
    # Bullet Health also adds a little damage (hidden effect in the original).
    return (7 + 3 * p_dmg) * (1 + 0.04 * p_bhp)


def bullet_speed(p: int) -> float:
    return 520 * (1 + 0.06 * p)


def reload_time(p: int) -> float:
    return 0.55 * 0.92**p


def bullet_hp(p: int) -> float:
    return 10 * (1 + 0.15 * p)


def max_health(p: int, level: int) -> float:
    return 50 + 20 * p + 2 * (level - 1)


def regen_rate(p: int) -> float:
    """Fraction of max HP regenerated per second."""
    return 0.003 + 0.004 * p


def move_speed(p: int, level: int) -> float:
    return 230 * (1 + 0.05 * p) * (1 - 0.0012 * (level - 1))


def body_damage(p: int) -> float:
    return 10 + 6 * p


def tank_radius(level: int) -> float:
    return 24 * (1 + 0.004 * (level - 1))


# --- Shapes ----------------------------------------------------------------

SHAPES = {
    #            hp    xp  gems sides radius toughness body_dmg
    "square": dict(hp=10, xp=10, gems=0, sides=4, radius=22, toughness=5, body=2),
    "triangle": dict(hp=30, xp=25, gems=0, sides=3, radius=24, toughness=8, body=4),
    "pentagon": dict(hp=100, xp=130, gems=0, sides=5, radius=34, toughness=12, body=6),
    "alpha": dict(hp=3000, xp=3000, gems=50, sides=5, radius=110, toughness=30, body=15),
}
SHAPE_COUNTS = {"square": 320, "triangle": 140, "pentagon": 60, "alpha": 2}
SHINY_CHANCE = 1 / 50
SHINY_XP_MULT = 10
SHINY_GEMS = 25


# --- Gems ------------------------------------------------------------------


def kill_gems(victim_level: int) -> int:
    """Gems for destroying another tank (original: 5-20+ per kill)."""
    return 5 + victim_level // 5


def kill_xp(victim_score: float) -> float:
    return max(20.0, victim_score / 2)


def death_gems(score: float) -> int:
    return int(score // 200)


def rebirth_gems(rebirths_done: int) -> int:
    return 10000 * (rebirths_done + 1)


def rebirth_xp_mult(rebirths: int) -> float:
    return 1 + 0.05 * rebirths


STARTING_GEMS = 25000  # like the original's HEADSTART code


# --- Ranks -----------------------------------------------------------------

RANK_COUNT = 20


def rank_threshold(rank: int) -> int:
    """Cumulative score (all runs) needed for `rank` (1..20)."""
    return 5000 * (rank - 1) ** 2


def rank_for_score(total_score: float) -> int:
    rank = 1
    while rank < RANK_COUNT and total_score >= rank_threshold(rank + 1):
        rank += 1
    return rank


def rank_name(rank: int) -> str:
    if rank <= 10:
        return f"Bronze {rank}"
    if rank <= 14:
        return f"Silver {rank - 10}"
    if rank <= 17:
        return f"Gold {rank - 14}"
    if rank <= 19:
        return f"Diamond {rank - 17}"
    return "Champion"


BLAST_LORD_RANK = 10


# --- Quests ----------------------------------------------------------------
# (id, text, event, target, mode, reward). mode "sum" adds up, "max" keeps best.
# reward is a gem amount or a tank name string.

DAILY_POOL = [
    ("d_sq", "Destroy 150 squares", "shape:square", 150, "sum", 1500),
    ("d_tri", "Destroy 60 triangles", "shape:triangle", 60, "sum", 2000),
    ("d_pent", "Destroy 15 pentagons", "shape:pentagon", 15, "sum", 2500),
    ("d_kill", "Destroy 5 tanks", "kill", 5, "sum", 3000),
    ("d_lvl30", "Reach level 30", "level", 30, "max", 2000),
    ("d_lvl45", "Reach level 45", "level", 45, "max", 4000),
    ("d_score", "Score 20,000 in one run", "score", 20000, "max", 3000),
    ("d_evo", "Evolve 3 times", "evolve", 3, "sum", 2000),
    ("d_shiny", "Destroy a shiny shape", "shape:shiny", 1, "sum", 5000),
]
WEEKLY_POOL = [
    ("w_kill", "Destroy 50 tanks", "kill", 50, "sum", 20000),
    ("w_lvl90", "Reach level 90", "level", 90, "max", 25000),
    ("w_pent", "Destroy 200 pentagons", "shape:pentagon", 200, "sum", 20000),
    ("w_alpha", "Destroy 3 Alpha Pentagons", "shape:alpha", 3, "sum", 25000),
]
UNIQUE_QUESTS = [
    ("u_twin", "Destroy 1,000 triangles", "shape:triangle", 1000, "sum", "Twinblast"),
    ("u_lvl105", "Reach level 105", "level", 105, "max", 30000),
    ("u_kill100", "Destroy 100 tanks", "kill", 100, "sum", 50000),
]
DAILY_COUNT = 3
WEEKLY_COUNT = 2


# --- Codes (from the original game's code list) ----------------------------
# value: ("gems", n) | ("xp", n) | ("spins", n)

CODES = {
    "HEADSTART": ("gems", 25000),
    "NEWCURRENCY": ("gems", 50000),
    "PREPAREYOURGEMS": ("gems", 20000),
    "TANKQUESTS": ("gems", 25000),
    "NONUKES": ("gems", 25000),
    "HAVEFUN": ("xp", 200000),
    "REBALANCEAGAIN": ("xp", 250000),
    "NEWPORTALS": ("xp", 200000),
    "APOLLO": ("xp", 500000),
    "TANKGAME2": ("spins", 1),
    "THANKSGIVING": ("spins", 2),
}


# --- Prize wheel -----------------------------------------------------------
# (label, kind, value, weight)

WHEEL_PRIZES = [
    ("500 Gems", "gems", 500, 25),
    ("1,000 Gems", "gems", 1000, 22),
    ("2,500 Gems", "gems", 2500, 16),
    ("5,000 Gems", "gems", 5000, 8),
    ("Head Start", "xp", 15000, 14),
    ("Big Head Start", "xp", 60000, 6),
    ("1 Spin", "spins", 1, 8),
    ("ULTRASHIP!", "tank", "Ultraship", 1),
]


# --- Skins -----------------------------------------------------------------

SKINS = [
    ("Classic", (0, 178, 225), 0),
    ("Emerald", (0, 200, 110), 5000),
    ("Bubblegum", (255, 120, 200), 8000),
    ("Sunset", (255, 150, 50), 8000),
    ("Royal", (150, 90, 230), 10000),
    ("Gold", (240, 200, 40), 15000),
    ("Shadow", (60, 60, 75), 25000),
    ("Rainbow", None, 50000),  # animated
]
