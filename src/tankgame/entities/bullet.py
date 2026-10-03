import math


class Bullet:
    """A projectile. Also used for freeze/flame particles and orbiters."""

    def __init__(self, owner, x, y, vx, vy, radius, damage, hp, life, kind="bullet"):
        self.owner = owner
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.radius = radius
        self.damage = damage
        self.hp = self.max_hp = hp
        self.life = self.max_life = life
        self.kind = kind
        self.alive = True
        self.hit = set()          # ids of targets already hit
        self.cooldowns = {}       # orbiters: target id -> time until next hit
        self.slot = 0             # orbiters: slot index
        self.explode_radius = 0.0

    def update(self, dt: float) -> None:
        if self.kind == "orbiter":
            o = self.owner
            n = max(1, o.tdef["orbiters"])
            a = o.orbit_phase + self.slot * math.tau / n
            dist = o.radius * 2.3
            self.x = o.x + math.cos(a) * dist
            self.y = o.y + math.sin(a) * dist
            self.hp = min(self.max_hp, self.hp + self.max_hp * 0.1 * dt)
            for k in list(self.cooldowns):
                self.cooldowns[k] -= dt
                if self.cooldowns[k] <= 0:
                    del self.cooldowns[k]
            return
        if self.kind == "rocket":
            accel = 1 + 2.2 * dt
            self.vx *= accel
            self.vy *= accel
            sp = math.hypot(self.vx, self.vy)
            if sp > 1400:
                self.vx *= 1400 / sp
                self.vy *= 1400 / sp
        elif self.kind in ("freeze", "flame"):
            self.vx *= 1 - 2.5 * dt
            self.vy *= 1 - 2.5 * dt
            self.radius *= 1 + 1.8 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False


class Beam:
    """Visual for a railgun laser."""

    def __init__(self, x1, y1, x2, y2, width, color):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.width = width
        self.color = color
        self.life = self.max_life = 0.25


class Ring:
    """Visual for explosions and deaths."""

    def __init__(self, x, y, radius, color, life=0.3):
        self.x, self.y = x, y
        self.radius = radius
        self.color = color
        self.life = self.max_life = life
