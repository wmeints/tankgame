"""The tank entity shared by the player and the bots."""

import math
import random

from .. import config as C
from ..data import progression as P
from ..data.tanks import TANKS
from .bullet import Bullet


class Tank:
    """A tank with stats, levels, barrels and evolutions, steered by input or a `Brain`."""

    is_tank = True
    _next_id = 1

    def __init__(self, arena, name, pos, color, caps=None):
        self.id = Tank._next_id
        Tank._next_id += 1
        self.arena = arena
        self.name = name
        self.x, self.y = pos
        self.vx = self.vy = 0.0
        self.kx = self.ky = 0.0
        self.angle = 0.0
        self.color = color
        self.is_player = False
        self.brain = None
        self.xp_mult = 1.0

        self.score = 0.0
        self.level = 1
        self.points = dict.fromkeys(P.STATS, 0)
        self.caps = caps or dict.fromkeys(P.STATS, P.BASE_CAP)
        self.unspent = 0
        self.kills = 0

        self.move_x = self.move_y = 0.0
        self.firing = False
        self.alive = True
        self.immune = C.SPAWN_IMMUNITY
        self.flash = 0.0
        self.since_hit = 99.0
        self.slow_timer = 0.0
        self.burn_timer = 0.0
        self.burn_dps = 0.0
        self.burn_source = None
        self.alpha = 1.0
        self.still_time = 0.0
        self.orbit_phase = 0.0
        self.orbiters = []  # Bullet or float (respawn timer)
        self.last_attacker = None
        self.attacked_timer = 0.0
        self.evolutions = []  # names evolved into this run

        self.set_tank("Basic")
        self.hp = self.max_hp

    @classmethod
    def make_player(cls, arena, pos, color, caps, xp_mult):
        """Create the player's tank with its stat caps and XP multiplier."""
        tank = cls(arena, "You", pos, color, caps)
        tank.is_player = True
        tank.xp_mult = xp_mult
        return tank

    # --- progression ----------------------------------------------------
    def set_tank(self, name: str) -> None:
        """Switch to tank type `name`, resetting barrels and orbiters, keeping the HP fraction."""
        self.tank_name = name
        self.tdef = TANKS[name]
        self.timers = [b["delay"] * self._reload(b) for b in self.tdef["barrels"]]
        for o in self.orbiters:
            if isinstance(o, Bullet):
                o.alive = False
        self.orbiters = [0.5] * self.tdef["orbiters"]
        old_max = getattr(self, "max_hp", None)
        self.recompute()
        if old_max:
            self.hp = min(self.max_hp, self.hp * self.max_hp / old_max)

    def evolve(self, name: str) -> None:
        """Evolve into tank type `name` and record it in this run's evolutions."""
        self.evolutions.append(name)
        self.set_tank(name)

    def recompute(self) -> None:
        """Recalculate derived stats from level, stat points and the tank definition."""
        p = self.points
        t = self.tdef
        self.radius = P.tank_radius(self.level)
        self.max_hp = P.max_health(p["maxhp"], self.level) * t["hp"]
        self.regen = P.regen_rate(p["regen"])
        self.speed = P.move_speed(p["speed"], self.level) * t["speed"]
        self.body_damage = P.body_damage(p["body"]) * t["body"]
        self.toughness = 10 + self.body_damage * 0.5
        self.bullet_damage = P.bullet_damage(p["dmg"], p["bhp"])
        self.bullet_speed = P.bullet_speed(p["bspd"])
        self.bullet_hp = P.bullet_hp(p["bhp"])
        self.reload = P.reload_time(p["reload"])
        self.mass = self.radius**2 * (2.5 if t["grinder"] else 1.5)

    def _reload(self, barrel) -> float:
        return P.reload_time(self.points["reload"]) * barrel["reload"]

    def add_xp(self, amount: float) -> int:
        """Add score. Returns number of levels gained."""
        self.score += amount * self.xp_mult
        new_level = P.level_for_xp(self.score)
        gained = new_level - self.level
        if gained > 0:
            old_pts = P.stat_points_for_level(self.level)
            self.level = new_level
            self.unspent += P.stat_points_for_level(new_level) - old_pts
            old_max = self.max_hp
            self.recompute()
            self.hp += self.max_hp - old_max
        return gained

    def can_upgrade(self, stat: str) -> bool:
        """Return whether a point can be spent on `stat` (points left and below its cap)."""
        return self.unspent > 0 and self.points[stat] < self.caps[stat]

    def upgrade(self, stat: str) -> bool:
        """Spend a stat point on `stat` and return whether it was spent."""
        if not self.can_upgrade(stat):
            return False
        self.points[stat] += 1
        self.unspent -= 1
        old_max = self.max_hp
        self.recompute()
        self.hp += self.max_hp - old_max
        return True

    # --- simulation -----------------------------------------------------
    def update(self, dt: float) -> None:
        """Advance the tank one step: timers, movement, status effects, regen and firing."""
        self._tick_timers(dt)
        self._move(dt)
        self._tick_status_effects(dt)
        if not self.alive:  # burned to death
            return
        self._regenerate(dt)
        self._update_invisibility(dt)
        self._update_orbiters(dt)
        self._update_barrels(dt)

    def _tick_timers(self, dt: float) -> None:
        if self.immune > 0:
            self.immune -= dt
            # like Diep: shooting ends spawn protection early (after 1s)
            if self.firing and self.immune < C.SPAWN_IMMUNITY - 1:
                self.immune = 0
        if self.flash > 0:
            self.flash -= dt
        self.since_hit += dt
        if self.attacked_timer > 0:
            self.attacked_timer -= dt

    def _move(self, dt: float) -> None:
        mag = math.hypot(self.move_x, self.move_y)
        mx, my = (self.move_x / mag, self.move_y / mag) if mag > 0 else (0.0, 0.0)
        speed = self.speed * (0.5 if self.slow_timer > 0 else 1.0)
        k = min(1.0, 8 * dt)
        self.vx += (mx * speed - self.vx) * k
        self.vy += (my * speed - self.vy) * k
        self.x += (self.vx + self.kx) * dt
        self.y += (self.vy + self.ky) * dt
        decay = math.exp(-4 * dt)
        self.kx *= decay
        self.ky *= decay
        r = self.radius
        self.x = min(max(self.x, r), C.ARENA_SIZE - r)
        self.y = min(max(self.y, r), C.ARENA_SIZE - r)

    def _tick_status_effects(self, dt: float) -> None:
        if self.slow_timer > 0:
            self.slow_timer -= dt
        if self.burn_timer > 0:
            self.burn_timer -= dt
            self.take_damage(self.burn_dps * dt, self.burn_source, flash=False)

    def _regenerate(self, dt: float) -> None:
        if self.hp < self.max_hp:
            rate = self.regen + (0.05 if self.since_hit > 30 else 0.0)
            self.hp = min(self.max_hp, self.hp + self.max_hp * rate * dt)

    def _update_invisibility(self, dt: float) -> None:
        if not self.tdef["invis"]:
            self.alpha = 1.0
            return
        moving = math.hypot(self.vx, self.vy) > 40
        if moving or self.firing:
            self.still_time = 0
            self.alpha = min(1.0, self.alpha + 4 * dt)
        else:
            self.still_time += dt
            if self.still_time > 1.0:
                self.alpha = max(0.08, self.alpha - 0.6 * dt)

    def _update_orbiters(self, dt: float) -> None:
        """Each slot holds a live orbiter Bullet, or a float counting down to its respawn."""
        self.orbit_phase += 2.2 * dt
        for i, o in enumerate(self.orbiters):
            if isinstance(o, Bullet):
                if not o.alive:
                    self.orbiters[i] = 3.0
            elif o - dt <= 0:
                self.orbiters[i] = self._spawn_orbiter(i)
            else:
                self.orbiters[i] = o - dt

    def _spawn_orbiter(self, slot: int) -> Bullet:
        b = Bullet(
            owner=self,
            x=self.x,
            y=self.y,
            vx=0,
            vy=0,
            radius=self.radius * 0.45,
            damage=self.bullet_damage * 0.6,
            hp=self.bullet_hp * 3,
            life=1e9,
            kind="orbiter",
        )
        b.slot = slot
        self.arena.bullets.append(b)
        return b

    def _update_barrels(self, dt: float) -> None:
        for i, b in enumerate(self.tdef["barrels"]):
            rel = self._reload(b)
            if self.firing:
                self.timers[i] -= dt
                while self.timers[i] <= 0:
                    self.timers[i] += rel
                    self.fire(b)
            else:
                self.timers[i] = max(self.timers[i] - dt, b["delay"] * rel)

    def muzzle(self, b):
        """Locate the muzzle of barrel `b`.

        Returns
        -------
        tuple of float
            The firing angle in radians and the muzzle's world x and y.
        """
        a = self.angle + math.radians(b["angle"])
        ca, sa = math.cos(a), math.sin(a)
        length = b["length"] * self.radius
        off = b["offset"] * self.radius
        return a, self.x + ca * length - sa * off, self.y + sa * length + ca * off

    def fire(self, b) -> None:
        """Fire barrel `b` once (bullets or a laser) and apply its recoil."""
        arena = self.arena
        a, mx, my = self.muzzle(b)
        if b["kind"] == "laser":
            rng = 900 * b["range"]
            arena.fire_laser(
                self, (mx, my), a, rng, self.bullet_damage * b["dmg"], b["width"] * self.radius
            )
        else:
            for _ in range(b["pellets"]):
                sa = a + math.radians(random.uniform(-b["spread"], b["spread"]) / 2)
                spd = (
                    self.bullet_speed
                    * b["speed"]
                    * (random.uniform(0.85, 1.1) if b["pellets"] > 1 else 1)
                )
                radius = b["width"] * self.radius * 0.5 * b["size"]
                life = 1.4 * b["range"]
                if b["kind"] in ("freeze", "flame"):
                    radius *= 0.6
                bl = Bullet(
                    owner=self,
                    x=mx,
                    y=my,
                    vx=math.cos(sa) * spd + self.vx * 0.3,
                    vy=math.sin(sa) * spd + self.vy * 0.3,
                    radius=radius,
                    damage=self.bullet_damage * b["dmg"],
                    hp=self.bullet_hp * b["bhp"],
                    life=life,
                    kind=b["kind"],
                )
                if b["kind"] == "rocket":
                    bl.explode_radius = 70 * b["size"] + self.radius
                arena.bullets.append(bl)
        push = b["recoil"] * b["width"] * 9
        self.kx -= math.cos(a) * push
        self.ky -= math.sin(a) * push
        if self.is_player:
            arena.sfx("shoot" if b["kind"] not in ("freeze", "flame") else None)

    def take_damage(self, amount: float, source, arena=None, flash=True) -> None:
        """Lose HP unless spawn-immune, and notify the arena if this kills the tank.

        `arena` is unused and only keeps the signature in line with `Shape.take_damage`.
        """
        if not self.alive or self.immune > 0:
            return
        if self.is_player:
            amount *= self.arena.player_hurt
        self.hp -= amount
        self.since_hit = 0
        if flash:
            self.flash = 0.08
        if source is not None and source is not self and getattr(source, "is_tank", False):
            self.last_attacker = source
            self.attacked_timer = 5.0
        if self.tdef["invis"]:
            self.alpha = 1.0
            self.still_time = 0
        if self.hp <= 0:
            self.alive = False
            for o in self.orbiters:
                if isinstance(o, Bullet):
                    o.alive = False
            self.arena.on_tank_killed(self, source)
