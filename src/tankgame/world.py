"""The arena simulation: tanks, shapes, bullets, collisions, kills and rewards.

Independent of rendering so it can run headless (tests / --simulate).
"""

import math
import random

from . import config as C
from . import meta
from .ai import Brain, bot_level, random_name, DIFFICULTY
from .data import progression as P
from .entities.bullet import Beam, Ring
from .entities.shape import Shape
from .entities.tank import Tank
from .spatial import Grid

BULLET_VS_BULLET = {"bullet", "spike", "rocket", "orbiter"}


class World:
    def __init__(self, profile: dict, sfx=None, autoplay=False):
        self.profile = profile
        self.difficulty = profile.get("difficulty", "normal")
        self.player_hurt = DIFFICULTY[self.difficulty]["hurt"]
        self._sfx = sfx
        self.time = 0.0
        self.tanks: list[Tank] = []
        self.shapes: list[Shape] = []
        self.bullets = []
        self.beams: list[Beam] = []
        self.rings: list[Ring] = []
        self.toasts = []                 # [text, ttl, color]
        self.solids = Grid()
        self.bullet_grid = Grid()
        self.bot_respawns = []
        self.dead = False
        self.killer_name = ""
        self.run_kills = 0
        self.run_gems = 0
        self.rebirthed = False
        self._score_tick = 0.0
        self._shape_tick = 0.0

        caps = {s: meta.stat_cap(profile, s) for s in P.STATS}
        self.player = Tank(self, "You", *self.random_spawn(), self.skin_color(0),
                           is_player=True, caps=caps,
                           xp_mult=P.rebirth_xp_mult(profile["rebirths"]))
        if autoplay:
            self.player.brain = Brain(self.player, "normal")
        self.tanks.append(self.player)
        if profile["pending_xp"]:
            self.player.add_xp(profile["pending_xp"] / self.player.xp_mult)
            self.toast(f"Head start: +{profile['pending_xp']:,} XP!", C.XP_YELLOW)
            profile["pending_xp"] = 0

        for kind, n in P.SHAPE_COUNTS.items():
            for _ in range(n):
                self.spawn_shape(kind)
        for _ in range(C.BOT_COUNT):
            self.spawn_bot(far=True)

    # --- helpers --------------------------------------------------------
    def skin_color(self, t):
        from .render import rainbow
        for name, col, _price in P.SKINS:
            if name == self.profile.get("skin"):
                return col if col else rainbow(t)
        return C.PLAYER_COLOR

    def sfx(self, name):
        if self._sfx:
            self._sfx.play(name)

    def toast(self, text, color=C.TEXT, ttl=3.0):
        self.toasts.append([text, ttl, color])
        self.toasts = self.toasts[-5:]

    def random_spawn(self):
        while True:
            x = random.uniform(300, C.ARENA_SIZE - 300)
            y = random.uniform(300, C.ARENA_SIZE - 300)
            if math.hypot(x - C.ARENA_SIZE / 2, y - C.ARENA_SIZE / 2) > C.NEST_RADIUS + 200:
                return x, y

    def spawn_shape(self, kind):
        c = C.ARENA_SIZE / 2
        if kind == "alpha":
            a, d = random.uniform(0, math.tau), random.uniform(0, C.NEST_RADIUS * 0.6)
            x, y = c + math.cos(a) * d, c + math.sin(a) * d
        elif kind == "pentagon" and random.random() < 0.6:
            a, d = random.uniform(0, math.tau), random.uniform(0, C.NEST_RADIUS)
            x, y = c + math.cos(a) * d, c + math.sin(a) * d
        else:
            while True:
                x = random.uniform(60, C.ARENA_SIZE - 60)
                y = random.uniform(60, C.ARENA_SIZE - 60)
                if math.hypot(x - c, y - c) > C.NEST_RADIUS or random.random() < 0.15:
                    break
        shiny = kind != "alpha" and random.random() < P.SHINY_CHANCE
        self.shapes.append(Shape(kind, x, y, shiny))

    def spawn_bot(self, far=False):
        for _ in range(30):
            x, y = self.random_spawn()
            p = self.player
            if math.hypot(x - p.x, y - p.y) > (1400 if far else 900):
                break
        extra = DIFFICULTY[self.difficulty]["caps"]
        caps = {s: max(5, min(P.MAX_CAPS[s], P.BASE_CAP + extra)) for s in P.STATS}
        bot = Tank(self, random_name(), x, y, C.ENEMY_COLOR, caps=caps)
        bot.brain = Brain(bot, self.difficulty)
        lvl = bot_level(self.difficulty, self.player.level)
        bot.add_xp(P.total_xp_for_level(lvl) + random.uniform(0, P.xp_to_next(lvl) * 0.9))
        bot.brain.grow_up()
        bot.hp = bot.max_hp
        bot.immune = 2.0
        self.tanks.append(bot)

    def shapes_near(self, x, y, r):
        return [e for e in self.solids.query_unique(x, y, r) if not e.is_tank and e.alive]

    def evolution_choices(self):
        from .data.tanks import evolution_options
        return evolution_options(self.player.tank_name, self.player.level)

    # --- events ---------------------------------------------------------
    def quest(self, event, amount=1):
        for msg in meta.quest_event(self.profile, event, amount):
            self.toast(msg, C.GEM_COLOR, 5)
            self.sfx("gem")

    def player_evolve(self, name):
        self.player.evolve(name)
        self.sfx("evolve")
        self.toast(f"Evolved into {name}!", C.XP_YELLOW)
        self.quest("evolve")

    def give_gems(self, n, why=""):
        if n <= 0:
            return
        self.profile["gems"] += n
        self.run_gems += n
        self.toast(f"+{n} gems {why}".strip(), C.GEM_COLOR)
        self.sfx("gem")

    def credit_xp(self, tank, xp):
        old = tank.level
        gained = tank.add_xp(xp)
        if gained:
            if tank.brain and not tank.is_player:
                tank.brain.grow_up()
            elif tank.is_player:
                self.sfx("levelup")
                self.quest("level", tank.level)
                if tank.brain:  # autoplay
                    tank.brain.grow_up()
                if tank.level >= P.REBIRTH_LEVEL > old:
                    self.toast("Level 150! Press R to Rebirth", C.XP_YELLOW, 8)

    def on_shape_killed(self, shape, source):
        if source is None or not getattr(source, "is_tank", False):
            return
        self.credit_xp(source, shape.xp)
        if source.is_player:
            self.profile["shape_counts"][shape.kind] += 1
            self.quest("shape:" + shape.kind)
            if shape.shiny:
                self.profile["shape_counts"]["shiny"] += 1
                self.quest("shape:shiny")
            self.give_gems(shape.gems, "(shiny!)" if shape.shiny else "")
            self.sfx("hit")

    def on_tank_killed(self, victim, killer):
        self.rings.append(Ring(victim.x, victim.y, victim.radius * 2, victim.color, 0.5))
        if getattr(killer, "is_tank", False) and killer.alive:
            killer.kills += 1
            self.credit_xp(killer, P.kill_xp(victim.score))
            if killer.is_player:
                self.run_kills += 1
                self.sfx("kill")
                self.toast(f"You destroyed {victim.name}!", C.WHITE)
                self.give_gems(P.kill_gems(victim.level))
                self.quest("kill")
        if victim.is_player:
            self.dead = True
            self.killer_name = killer.name if getattr(killer, "is_tank", False) else (
                f"a {killer.kind}" if killer is not None else "something")
            self.sfx("death")
        else:
            self.bot_respawns.append(random.uniform(3, 8))

    def fire_laser(self, owner, x, y, angle, rng, damage, width):
        ca, sa = math.cos(angle), math.sin(angle)
        ex, ey = x + ca * rng, y + sa * rng
        self.beams.append(Beam(x, y, ex, ey, width, C.LASER_COLOR))
        seen = set()
        steps = int(rng // C.GRID_CELL) + 1
        for i in range(steps + 1):
            px, py = x + ca * i * C.GRID_CELL, y + sa * i * C.GRID_CELL
            for e in self.solids.query(px, py, C.GRID_CELL):
                if id(e) in seen or e is owner or not e.alive:
                    continue
                seen.add(id(e))
                # distance from e to the segment
                t = max(0.0, min(rng, (e.x - x) * ca + (e.y - y) * sa))
                cx, cy = x + ca * t, y + sa * t
                if math.hypot(e.x - cx, e.y - cy) <= e.radius + width / 2:
                    e.take_damage(damage, owner, self)
        if owner.is_player:
            self.sfx("shoot")

    def explode(self, b):
        self.rings.append(Ring(b.x, b.y, b.explode_radius, C.FLAME_COLOR, 0.3))
        for e in self.solids.query_unique(b.x, b.y, b.explode_radius):
            if e is b.owner or not e.alive:
                continue
            if math.hypot(e.x - b.x, e.y - b.y) <= b.explode_radius + e.radius:
                e.take_damage(b.damage, b.owner, self)

    def rebirth(self):
        p = self.player
        if p.level < P.REBIRTH_LEVEL or self.dead:
            return False
        gems = P.rebirth_gems(self.profile["rebirths"])
        self.profile["rebirths"] += 1
        self.give_gems(gems, "for Rebirth")
        self.rebirthed = True
        self.dead = True
        self.killer_name = ""
        return True

    # --- update ---------------------------------------------------------
    def update(self, dt):
        self.time += dt
        if not self.dead:
            self._score_tick -= dt
            if self._score_tick <= 0:
                self._score_tick = 1.0
                self.quest("score", self.player.score)

        for t in self.tanks:
            if t.brain and t.alive:
                t.brain.update(dt)
                if not t.is_player:
                    # trickle XP: simulates the farming other players do off-screen
                    self.credit_xp(t, (1.5 + t.level * 0.15) * dt)
        for t in self.tanks:
            if t.alive and not (t.is_player and self.dead):
                t.update(dt)
        if not self.dead and self.player.alive:
            self.player.color = self.skin_color(self.time)
        for b in self.bullets:
            if b.alive and b.kind == "orbiter" and not b.owner.alive:
                b.alive = False
            b.update(dt)
            if not b.alive and b.kind == "rocket" and b.explode_radius:
                self.explode(b)
                b.explode_radius = 0
        for s in self.shapes:
            s.update(dt)

        self.collide(dt)

        self.tanks = [t for t in self.tanks if t.alive or t.is_player]
        self.shapes = [s for s in self.shapes if s.alive]
        self.bullets = [b for b in self.bullets if b.alive]
        for lst in (self.beams, self.rings):
            for v in lst:
                v.life -= dt
        self.beams = [v for v in self.beams if v.life > 0]
        self.rings = [v for v in self.rings if v.life > 0]
        for tst in self.toasts:
            tst[1] -= dt
        self.toasts = [tst for tst in self.toasts if tst[1] > 0]

        self._shape_tick -= dt
        if self._shape_tick <= 0:
            self._shape_tick = 0.5
            counts = {k: 0 for k in P.SHAPE_COUNTS}
            for s in self.shapes:
                counts[s.kind] += 1
            for kind, n in P.SHAPE_COUNTS.items():
                for _ in range(min(4, n - counts[kind])):
                    self.spawn_shape(kind)

        for i in range(len(self.bot_respawns)):
            self.bot_respawns[i] -= dt
        while self.bot_respawns and min(self.bot_respawns) <= 0:
            self.bot_respawns.remove(min(self.bot_respawns))
            self.spawn_bot()

    def collide(self, dt):
        solids = self.solids
        solids.clear()
        for s in self.shapes:
            if s.alive:
                solids.insert(s)
        for t in self.tanks:
            if t.alive:
                solids.insert(t)

        # bullets vs bullets
        bg = self.bullet_grid
        bg.clear()
        for b in self.bullets:
            if b.alive and (b.kind in BULLET_VS_BULLET or b.kind == "freeze"):
                bg.insert(b)
        for cell in bg.cells.values():
            n = len(cell)
            if n < 2:
                continue
            for i in range(n):
                a = cell[i]
                for j in range(i + 1, n):
                    b = cell[j]
                    if a.owner is b.owner or not (a.alive and b.alive):
                        continue
                    rr = a.radius + b.radius
                    dx, dy = a.x - b.x, a.y - b.y
                    if dx * dx + dy * dy > rr * rr:
                        continue
                    if a.kind == "freeze" or b.kind == "freeze":
                        if a.kind == "freeze" and b.kind != "freeze":
                            b.hp -= 8
                        elif b.kind == "freeze" and a.kind != "freeze":
                            a.hp -= 8
                    else:
                        ad, bd = a.damage, b.damage
                        a.hp -= bd * 0.6
                        b.hp -= ad * 0.6
                    for x in (a, b):
                        if x.hp <= 0:
                            x.alive = False

        # bullets vs shapes / tanks
        for b in self.bullets:
            if not b.alive:
                continue
            for e in solids.query(b.x, b.y, b.radius):
                if not b.alive:
                    break
                if e is b.owner or not e.alive:
                    continue
                rr = b.radius + e.radius
                dx, dy = e.x - b.x, e.y - b.y
                if dx * dx + dy * dy > rr * rr:
                    continue
                if e.is_tank and e.immune > 0:
                    continue
                key = id(e)
                if b.kind == "orbiter":
                    if key in b.cooldowns:
                        continue
                    b.cooldowns[key] = 0.25
                elif key in b.hit:
                    continue
                else:
                    b.hit.add(key)
                if b.kind == "rocket":
                    self.explode(b)
                    b.explode_radius = 0
                    b.alive = False
                    break
                e.take_damage(b.damage, b.owner, self)
                if e.is_tank:
                    if b.kind == "freeze":
                        e.slow_timer = 1.0
                    elif b.kind == "flame":
                        e.burn_timer = 2.0
                        e.burn_dps = max(e.burn_dps if e.burn_timer > 0 else 0, b.damage * 4)
                        e.burn_source = b.owner
                # knock the target a little
                d = math.sqrt(dx * dx + dy * dy) or 1
                push = 40 * b.radius / max(10.0, e.radius)
                e.kx += dx / d * push
                e.ky += dy / d * push
                b.hp -= e.toughness
                if b.hp <= 0:
                    b.alive = False

        # tank body collisions
        for t in self.tanks:
            if not t.alive:
                continue
            for e in solids.query_unique(t.x, t.y, t.radius):
                if e is t or not e.alive or (e.is_tank and e.id < t.id):
                    continue
                rr = t.radius + e.radius
                dx, dy = e.x - t.x, e.y - t.y
                d2 = dx * dx + dy * dy
                if d2 >= rr * rr:
                    continue
                d = math.sqrt(d2) or 1
                overlap = rr - d
                nx, ny = dx / d, dy / d
                total = t.mass + e.mass
                ft, fe = e.mass / total, t.mass / total
                t.x -= nx * overlap * ft
                t.y -= ny * overlap * ft
                e.x += nx * overlap * fe
                e.y += ny * overlap * fe
                t.kx -= nx * 120 * ft
                t.ky -= ny * 120 * ft
                e.kx += nx * 120 * fe
                e.ky += ny * 120 * fe
                e.take_damage(t.body_damage * 3 * dt, t, self)
                t.take_damage(e.body_damage * 3 * dt, e, self)
