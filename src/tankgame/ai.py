"""Bot tanks: they stand in for the other players of the online game."""

import math
import random

from . import config as C
from .data import progression as P
from .data.tanks import evolution_options

PERSONALITIES = {
    "sniper": dict(
        tanks=[
            "Scout",
            "Hitman",
            "Ace",
            "Watcher",
            "Railgun",
            "Double Railgun",
            "Wrath",
            "Fury",
            "Shadow",
            "Intruder",
            "Powerhouse",
            "Tundra",
        ],
        stats=["bspd", "dmg", "reload", "bhp", "speed", "maxhp", "regen", "body"],
        distance=550,
    ),
    "spammer": dict(
        tanks=[
            "Spammer",
            "Thunder",
            "Storm",
            "Ultra-Thunder",
            "Godfather",
            "Blaster",
            "Machinima",
            "Beastmode",
            "Sparta",
            "Eater",
            "Shadow",
            "Splitstorm",
            "Trilord",
            "Orchestra",
        ],
        stats=["reload", "dmg", "bhp", "bspd", "maxhp", "speed", "regen", "body"],
        distance=330,
    ),
    "melee": dict(
        tanks=[
            "Grinder",
            "Shredder",
            "Fuse",
            "Smashinator",
            "Plower",
            "Mega Shredder",
            "Apollo",
            "Turbine",
        ],
        stats=["body", "maxhp", "speed", "regen", "dmg", "reload", "bhp", "bspd"],
        distance=0,
    ),
    "heavy": dict(
        tanks=[
            "Double",
            "Triway",
            "Triple",
            "Side Triple",
            "Orchestra",
            "Eater",
            "Devourer",
            "Railgun",
            "Spiker",
            "Double Spiker",
            "Powerhouse",
            "Tundra",
        ],
        stats=["maxhp", "dmg", "reload", "bhp", "regen", "bspd", "speed", "body"],
        distance=360,
    ),
    "frost": dict(
        tanks=["Freezer", "Double Freezer", "Triple Freezer", "Mega Freezer", "Flame", "Inferno"],
        stats=["dmg", "reload", "maxhp", "speed", "regen", "bhp", "body", "bspd"],
        distance=110,
    ),
    "rocket": dict(
        tanks=[
            "Slide",
            "Apex",
            "Rocket",
            "Guardian",
            "Blast Lord",
            "Phoenix",
            "Scout",
            "Buckshot",
            "Double Buckshot",
            "Megashot",
        ],
        stats=["dmg", "reload", "bspd", "maxhp", "speed", "bhp", "regen", "body"],
        distance=300,
    ),
}
STAT_WEIGHTS = [5, 4, 4, 3, 2, 2, 1, 1]

DIFFICULTY = {
    # aim: aim error, react: seconds between decisions, bully: won't hunt tanks this many
    # levels lower, caps: extra stat caps, above: max bot level above the player,
    # newbie: won't hunt the player below this level (unless attacked),
    # hurt: multiplier on damage the player takes
    "easy": dict(aim=0.22, react=0.5, bully=15, caps=-1, above=25, newbie=20, hurt=0.5),
    "normal": dict(aim=0.09, react=0.3, bully=30, caps=0, above=45, newbie=10, hurt=0.8),
    "hard": dict(aim=0.03, react=0.15, bully=999, caps=2, above=75, newbie=0, hurt=1.0),
}

_PRE = [
    "xX",
    "Pro",
    "Epic",
    "Mega",
    "Super",
    "Dark",
    "Ultra",
    "Noob",
    "Turbo",
    "Sir",
    "Captain",
    "Sneaky",
    "Lil",
    "Big",
    "Toxic",
    "Golden",
    "Crazy",
    "Iron",
]
_MID = [
    "Tank",
    "Blaster",
    "Gamer",
    "Sniper",
    "Builder",
    "Ninja",
    "Dragon",
    "Shooter",
    "Panda",
    "Destroyer",
    "Wolf",
    "Bacon",
    "Robo",
    "Rocket",
    "Pixel",
    "Cannon",
    "Diep",
]
_SUF = ["", "", "_Xx", "123", "2015", "YT", "_TTV", "9000", "_Pro", "77", "_RBX", "xD"]


def random_name() -> str:
    return random.choice(_PRE) + random.choice(_MID) + random.choice(_SUF)


def bot_level(difficulty: str, player_level: int) -> int:
    top = min(P.MAX_LEVEL, max(20, player_level + DIFFICULTY[difficulty]["above"]))
    return 1 + int((top - 1) * random.random() ** 1.6)


class Brain:
    def __init__(self, tank, difficulty: str):
        self.tank = tank
        self.diff = DIFFICULTY[difficulty]
        self.personality = random.choice(list(PERSONALITIES))
        self.prefs = PERSONALITIES[self.personality]
        self.think_timer = 0.0
        self.target = None
        self.mode = "wander"
        self.waypoint = None
        self.aim_err = 0.0
        self.strafe = random.choice((-1, 1))

    # --- build choices --------------------------------------------------
    def spend_points(self) -> None:
        t = self.tank
        order = self.prefs["stats"]
        while t.unspent > 0:
            best, best_score = None, None
            for stat, w in zip(order, STAT_WEIGHTS, strict=True):
                if t.points[stat] >= t.caps[stat]:
                    continue
                score = t.points[stat] / w
                if best is None or score < best_score:
                    best, best_score = stat, score
            if best is None:
                break
            t.upgrade(best)

    def choose_evolution(self) -> bool:
        t = self.tank
        opts = evolution_options(t.tank_name, t.level)
        if not opts:
            return False
        names = [o["name"] for o in opts]
        for pref in self.prefs["tanks"]:
            if pref in names and random.random() < 0.85:
                t.evolve(pref)
                return True
        non_wild = [o for o in opts if "*" not in o["parents"]] or opts
        if random.random() < 0.15 or len(non_wild) == len(opts):
            t.evolve(random.choice(opts)["name"])
        else:
            t.evolve(random.choice(non_wild)["name"])
        return True

    def grow_up(self) -> None:
        """Evolve and spend points until nothing is left to do."""
        self.spend_points()
        while self.choose_evolution():
            pass
        self.spend_points()

    # --- behaviour ------------------------------------------------------
    def visible(self, other, dist) -> bool:
        return other.alpha > 0.35 or dist < 200

    def think(self) -> None:  # noqa: C901, PLR0912, PLR0915
        t = self.tank
        arena = t.arena
        hp_ratio = t.hp / t.max_hp
        view = 900 * t.tdef["fov"]
        near_tanks = [
            o
            for o in arena.tanks
            if o is not t and o.alive and abs(o.x - t.x) < view and abs(o.y - t.y) < view
        ]
        threat, threat_d = None, 1e9
        prey, prey_score = None, 1e9
        for o in near_tanks:
            d = math.hypot(o.x - t.x, o.y - t.y)
            if not self.visible(o, d):
                continue
            stronger = o.level >= t.level + 15 or o.score > t.score * 3 + 2000
            if d < 600 and (stronger or (hp_ratio < 0.35 and d < 450)):
                if d < threat_d:
                    threat, threat_d = o, d
                continue
            if o.immune > 0:
                continue
            attacked_by = t.last_attacker is o and t.attacked_timer > 0
            if t.level - o.level > self.diff["bully"] and not attacked_by:
                continue
            if o.is_player and o.level < self.diff["newbie"] and not attacked_by:
                continue
            score = d - (300 if attacked_by else 0) + o.hp * 0.5
            if score < prey_score:
                prey, prey_score = o, score
        self.aim_err = random.gauss(0, self.diff["aim"])
        if threat is not None and (self.personality != "melee" or hp_ratio < 0.5):
            self.mode, self.target = "flee", threat
            return
        if prey is not None:
            self.mode, self.target = "hunt", prey
            return
        best, best_v = None, 0
        for s in arena.shapes_near(t.x, t.y, 750):
            if s.kind == "alpha" and t.level < 45:
                continue
            d = math.hypot(s.x - t.x, s.y - t.y)
            v = s.xp / (d + 150)
            if v > best_v:
                best, best_v = s, v
        if best is not None:
            self.mode, self.target = "farm", best
            return
        self.mode, self.target = "wander", None
        if (
            self.waypoint is None
            or math.hypot(self.waypoint[0] - t.x, self.waypoint[1] - t.y) < 150
        ):
            if t.level >= 45 and random.random() < 0.6:
                c = C.ARENA_SIZE / 2
                self.waypoint = (c + random.uniform(-700, 700), c + random.uniform(-700, 700))
            else:
                self.waypoint = (
                    random.uniform(200, C.ARENA_SIZE - 200),
                    random.uniform(200, C.ARENA_SIZE - 200),
                )

    def update(self, dt: float) -> None:
        t = self.tank
        self.think_timer -= dt
        if self.think_timer <= 0 or (self.target is not None and not self.target.alive):
            self.think_timer = self.diff["react"] * random.uniform(0.8, 1.3)
            self.think()
        if random.random() < dt * 0.4:
            self.strafe = -self.strafe
        tgt = self.target
        t.firing = False
        if tgt is None:
            if self.waypoint:
                t.move_x, t.move_y = self.waypoint[0] - t.x, self.waypoint[1] - t.y
                t.angle = math.atan2(t.move_y, t.move_x)
            return
        dx, dy = tgt.x - t.x, tgt.y - t.y
        d = math.hypot(dx, dy) or 1
        # lead the target
        lead = d / max(200.0, t.bullet_speed)
        ax = tgt.x + getattr(tgt, "vx", 0) * lead - t.x
        ay = tgt.y + getattr(tgt, "vy", 0) * lead - t.y
        t.angle = math.atan2(ay, ax) + self.aim_err
        ux, uy = dx / d, dy / d
        melee = self.personality == "melee" or not t.tdef["barrels"]
        if self.mode == "flee":
            t.move_x, t.move_y = -ux + -uy * self.strafe * 0.4, -uy + ux * self.strafe * 0.4
            t.firing = not melee and d < 700
        elif self.mode == "hunt":
            want = 0 if melee else self.prefs["distance"]
            if d > want + 60:
                t.move_x, t.move_y = ux - uy * self.strafe * 0.3, uy + ux * self.strafe * 0.3
            elif d < want - 60:
                t.move_x, t.move_y = -ux - uy * self.strafe * 0.5, -uy + ux * self.strafe * 0.5
            else:
                t.move_x, t.move_y = -uy * self.strafe, ux * self.strafe
            t.firing = not melee and d < 850 * t.tdef["fov"]
        else:  # farm
            want = 0 if melee else 200 + tgt.radius
            if d > want:
                t.move_x, t.move_y = ux, uy
            else:
                t.move_x, t.move_y = -uy * self.strafe * 0.4, ux * self.strafe * 0.4
            t.firing = not melee and d < 700
