import math
import random

from .. import config as C
from ..data import progression as P


class Shape:
    is_tank = False

    def __init__(self, kind: str, x: float, y: float, shiny: bool = False):
        spec = P.SHAPES[kind]
        self.kind = kind
        self.shiny = shiny
        self.x, self.y = x, y
        ang = random.uniform(0, math.tau)
        drift = random.uniform(4, 12) if kind != "alpha" else 3
        self.vx, self.vy = math.cos(ang) * drift, math.sin(ang) * drift
        self.kx = self.ky = 0.0
        self.angle = random.uniform(0, math.tau)
        self.spin = random.uniform(-0.4, 0.4)
        self.radius = spec["radius"]
        self.sides = spec["sides"]
        mult = 2 if shiny else 1
        self.max_hp = self.hp = spec["hp"] * mult
        self.xp = spec["xp"] * (P.SHINY_XP_MULT if shiny else 1)
        self.gems = spec["gems"] + (P.SHINY_GEMS if shiny else 0)
        self.toughness = spec["toughness"]
        self.body_damage = spec["body"]
        self.mass = self.radius ** 2 * 2
        self.alive = True
        self.flash = 0.0
        self.immune = 0.0
        self.color = C.SHINY_COLOR if shiny else {
            "square": C.SQUARE_COLOR, "triangle": C.TRIANGLE_COLOR,
            "pentagon": C.PENTAGON_COLOR, "alpha": C.PENTAGON_COLOR}[kind]

    def update(self, dt: float) -> None:
        self.angle += self.spin * dt
        self.x += (self.vx + self.kx) * dt
        self.y += (self.vy + self.ky) * dt
        decay = math.exp(-3 * dt)
        self.kx *= decay
        self.ky *= decay
        r = self.radius
        if self.x < r or self.x > C.ARENA_SIZE - r:
            self.vx = -self.vx
            self.x = min(max(self.x, r), C.ARENA_SIZE - r)
        if self.y < r or self.y > C.ARENA_SIZE - r:
            self.vy = -self.vy
            self.y = min(max(self.y, r), C.ARENA_SIZE - r)
        if self.flash > 0:
            self.flash -= dt

    def take_damage(self, amount: float, source, arena) -> None:
        if not self.alive:
            return
        self.hp -= amount
        self.flash = 0.08
        if self.hp <= 0:
            self.alive = False
            arena.on_shape_killed(self, source)

    def points(self, cx, cy, scale):
        """Polygon points in screen space."""
        out = []
        r = self.radius * scale
        for i in range(self.sides):
            a = self.angle + i * math.tau / self.sides
            out.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        return out
