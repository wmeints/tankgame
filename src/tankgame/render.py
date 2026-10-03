"""Drawing of world entities (Diep style: flat shapes with dark outlines)."""

import colorsys
import math

import pygame

from . import config as C


def rainbow(t: float):
    r, g, b = colorsys.hsv_to_rgb((t * 0.2) % 1.0, 0.7, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)


def _lighten(color, f):
    return tuple(min(255, int(c + (255 - c) * f)) for c in color)


def poly(surf, color, pts, outline_w):
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, C.darken(color), pts, max(1, outline_w))


def circle(surf, color, center, r, outline_w):
    r = max(1, int(r))
    pygame.draw.circle(surf, C.darken(color), center, r)
    pygame.draw.circle(surf, color, center, max(1, r - max(1, outline_w)))


def draw_tank_body(surf, tdef, x, y, r, angle, color, spin=0.0, flash=False):
    """Draw barrels, blades and body of a tank at screen position (x, y) with radius r."""
    ow = max(1, int(r * 0.12))
    barrel_col = _lighten(C.BARREL, 0.5) if flash else C.BARREL
    if tdef["grinder"]:
        n = tdef["grinder"]
        pts = []
        for i in range(n * 2):
            a = spin + i * math.pi / n
            rr = r * (1.45 if i % 2 == 0 else 1.05)
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        poly(surf, (90, 90, 95), pts, ow)
    for b in tdef["barrels"]:
        a = angle + math.radians(b["angle"])
        ca, sa = math.cos(a), math.sin(a)
        px, py = -sa, ca
        off = b["offset"] * r
        bx, by = x + px * off, y + py * off
        length = b["length"] * r
        w0 = b["width"] * r / 2
        w1 = w0 * (1.45 if b["flare"] else 1.0)
        if b["flare"]:
            w0 *= 0.75
        tx, ty = bx + ca * length, by + sa * length
        pts = [(bx + px * w0, by + py * w0), (tx + px * w1, ty + py * w1),
               (tx - px * w1, ty - py * w1), (bx - px * w0, by - py * w0)]
        col = barrel_col
        if b["kind"] == "laser":
            col = (190, 140, 200)
        elif b["kind"] == "freeze":
            col = (150, 190, 210)
        elif b["kind"] == "flame":
            col = (210, 150, 110)
        elif b["kind"] == "rocket":
            col = (170, 150, 150)
        poly(surf, col, pts, ow)
    body = _lighten(color, 0.6) if flash else color
    circle(surf, body, (x, y), r, ow)


class Camera:
    def __init__(self):
        self.x = self.y = C.ARENA_SIZE / 2
        self.zoom = 1.0
        self.shake = 0.0

    def to_screen(self, x, y):
        return ((x - self.x) * self.zoom + C.SCREEN_W / 2,
                (y - self.y) * self.zoom + C.SCREEN_H / 2)

    def to_world(self, sx, sy):
        return ((sx - C.SCREEN_W / 2) / self.zoom + self.x,
                (sy - C.SCREEN_H / 2) / self.zoom + self.y)

    def visible(self, x, y, r):
        sx, sy = self.to_screen(x, y)
        rr = r * self.zoom + 10
        return -rr < sx < C.SCREEN_W + rr and -rr < sy < C.SCREEN_H + rr


def draw_background(surf, cam):
    surf.fill(C.BG_OUTSIDE)
    x0, y0 = cam.to_screen(0, 0)
    x1, y1 = cam.to_screen(C.ARENA_SIZE, C.ARENA_SIZE)
    pygame.draw.rect(surf, C.BG, pygame.Rect(x0, y0, x1 - x0, y1 - y0))
    cx, cy = cam.to_screen(C.ARENA_SIZE / 2, C.ARENA_SIZE / 2)
    pygame.draw.circle(surf, C.BG_NEST, (cx, cy), C.NEST_RADIUS * cam.zoom)
    step = 50
    wx0, wy0 = cam.to_world(0, 0)
    gx = math.floor(wx0 / step) * step
    while True:
        sx, _ = cam.to_screen(gx, 0)
        if sx > C.SCREEN_W:
            break
        pygame.draw.line(surf, C.BG_GRID, (sx, 0), (sx, C.SCREEN_H))
        gx += step
    gy = math.floor(wy0 / step) * step
    while True:
        _, sy = cam.to_screen(0, gy)
        if sy > C.SCREEN_H:
            break
        pygame.draw.line(surf, C.BG_GRID, (0, sy), (C.SCREEN_W, sy))
        gy += step


def hp_bar(surf, x, y, w, frac):
    if frac >= 0.999:
        return
    rect = pygame.Rect(0, 0, w, 7)
    rect.center = (x, y)
    pygame.draw.rect(surf, (60, 60, 60), rect, border_radius=4)
    inner = rect.inflate(-2, -2)
    inner.width = max(1, int(inner.width * max(0.0, frac)))
    pygame.draw.rect(surf, C.HP_GREEN, inner, border_radius=3)


def draw_shape(surf, cam, s):
    sx, sy = cam.to_screen(s.x, s.y)
    col = _lighten(s.color, 0.6) if s.flash > 0 else s.color
    poly(surf, col, s.points(sx, sy, cam.zoom), max(1, int(3 * cam.zoom)))
    if s.hp < s.max_hp:
        hp_bar(surf, sx, sy + (s.radius + 12) * cam.zoom, s.radius * 2 * cam.zoom, s.hp / s.max_hp)


def draw_bullet(surf, cam, b, color):
    sx, sy = cam.to_screen(b.x, b.y)
    r = b.radius * cam.zoom
    ow = max(1, int(3 * cam.zoom))
    if b.kind == "freeze":
        f = b.life / b.max_life
        pygame.draw.circle(surf, _lighten(C.FREEZE_COLOR, 1 - f), (sx, sy), max(1, r))
    elif b.kind == "flame":
        f = b.life / b.max_life
        col = (255, int(80 + 150 * f), int(40 * f))
        pygame.draw.circle(surf, col, (sx, sy), max(1, r))
    elif b.kind == "spike":
        pts = []
        for i in range(12):
            a = b.life * 6 + i * math.pi / 6
            rr = r * (1.5 if i % 2 == 0 else 0.8)
            pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
        poly(surf, color, pts, ow)
    elif b.kind == "rocket":
        a = math.atan2(b.vy, b.vx)
        tail = (sx - math.cos(a) * r * 2, sy - math.sin(a) * r * 2)
        pygame.draw.line(surf, C.FLAME_COLOR, (sx, sy), tail, max(2, int(r)))
        circle(surf, color, (sx, sy), r, ow)
    elif b.kind == "orbiter":
        a = b.owner.orbit_phase * 2
        pts = [(sx + math.cos(a + i * math.tau / 3) * r * 1.3,
                sy + math.sin(a + i * math.tau / 3) * r * 1.3) for i in range(3)]
        poly(surf, color, pts, ow)
    else:
        circle(surf, color, (sx, sy), r, ow)


def draw_tank(surf, cam, t, color, time):
    sx, sy = cam.to_screen(t.x, t.y)
    r = t.radius * cam.zoom
    if t.immune > 0 and int(time * 8) % 2 == 0:
        color = _lighten(color, 0.45)
    if t.alpha < 0.999:
        size = int(r * 6) + 4
        tmp = pygame.Surface((size, size), pygame.SRCALPHA)
        draw_tank_body(tmp, t.tdef, size / 2, size / 2, r, t.angle, color,
                       spin=time * 4, flash=t.flash > 0)
        tmp.set_alpha(int(255 * t.alpha))
        surf.blit(tmp, (sx - size / 2, sy - size / 2))
    else:
        draw_tank_body(surf, t.tdef, sx, sy, r, t.angle, color, spin=time * 4, flash=t.flash > 0)
    return sx, sy, r
