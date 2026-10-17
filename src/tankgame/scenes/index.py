"""Tank index scene: a pannable map of the evolution tree, left to right by level."""

import functools
import math
from typing import override

import pygame

from .. import config as C
from .. import meta, ui
from .. import render as R
from ..data.tanks import ANY, TANKS
from .menu import BackScene

CARD_W, CARD_H = 300, 84
COL_PITCH, ROW_PITCH = CARD_W + 90, CARD_H + 18
MARGIN = 40
VIEW = pygame.Rect(0, 140, C.SCREEN_W, C.SCREEN_H - 140)
PAN_SPEED = 900  # pixels per second for held keys
PAN_KEYS = {
    pygame.K_LEFT: (-1, 0),
    pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0),
    pygame.K_d: (1, 0),
    pygame.K_UP: (0, -1),
    pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1),
    pygame.K_s: (0, 1),
}
EDGE_COLOR, HIGHLIGHT = (85, 85, 100), C.UI_ACCENT


def _place_column(names, rows):
    """Give each tank in one column a row near the mean row of its parents.

    Tanks are kept at least one row apart and the column is shifted so that,
    on average, tanks sit level with their parents. Tanks without a placed
    parent (the "any tank" evolutions) go at the bottom.
    """

    def desired(name):
        ys = [rows[p] for p in TANKS[name]["parents"] if p in rows]
        return sum(ys) / len(ys) if ys else math.inf

    linked = sorted((desired(n), n) for n in names)
    placed, prev = {}, -math.inf
    for want, name in linked:
        if want == math.inf:
            continue
        prev = placed[name] = max(want, prev + 1)
    if placed:
        shift = sum(placed[n] - desired(n) for n in placed) / len(placed)
        placed = {n: y - shift for n, y in placed.items()}
    bottom = max(placed.values(), default=-1)
    for want, name in linked:
        if want == math.inf:
            bottom = placed[name] = bottom + 1
    return placed


@functools.cache
def depth(name):
    """Return the number of evolutions on the longest path from Basic to a tank.

    An "any tank" parent counts as a level 15 tank, so its children sit at depth 2.
    """
    parents = TANKS[name]["parents"]
    return 1 + max((1 if p == ANY else depth(p) for p in parents), default=-1)


def layout():
    """Return the map rect of every tank card, one column per evolution step."""
    cols = {n: depth(n) for n in TANKS}
    rows: dict[str, float] = {}
    for col in range(max(cols.values()) + 1):
        rows.update(_place_column([n for n in TANKS if cols[n] == col], rows))
    top = min(rows.values())
    return {
        n: pygame.Rect(
            MARGIN + cols[n] * COL_PITCH,
            MARGIN + round((rows[n] - top) * ROW_PITCH),
            CARD_W,
            CARD_H,
        )
        for n in TANKS
    }


CARDS = layout()
MAP_W = max(r.right for r in CARDS.values()) + MARGIN
MAP_H = max(r.bottom for r in CARDS.values()) + MARGIN
EDGES = [(p, n) for n, t in TANKS.items() for p in t["parents"] if p != ANY]


def curve(a, b, steps=16):
    """Return points on an S-curve from `a` to `b` that leaves and enters horizontally."""
    (ax, ay), (bx, by) = a, b
    pts = []
    for i in range(steps + 1):
        s = i / steps
        ease = s * s * (3 - 2 * s)
        pts.append((ax + (bx - ax) * s, ay + (by - ay) * ease))
    return pts


class TankIndexScene(BackScene):
    """Pannable map of every tank, with lines from each tank to the ones it evolves into."""

    title = "Tank Index"

    def __init__(self, game):
        super().__init__(game)
        self.cam = pygame.Vector2(0, max(0, CARDS["Basic"].centery - VIEW.h // 2))
        self.dragging = False
        self.t = 0.0

    def pan_by(self, dx, dy):
        """Move the camera by (`dx`, `dy`) map pixels, clamped to the map."""
        self.cam.x = min(max(0, MAP_W - VIEW.w), max(0, self.cam.x + dx))
        self.cam.y = min(max(0, MAP_H - VIEW.h), max(0, self.cam.y + dy))

    def to_screen(self, rect):
        """Return a map rect moved to its screen position."""
        return rect.move(VIEW.x - round(self.cam.x), VIEW.y - round(self.cam.y))

    def hovered(self):
        """Return the name of the tank card under the mouse, or None."""
        pos = pygame.mouse.get_pos()
        if not VIEW.collidepoint(pos):
            return None
        return next((n for n, r in CARDS.items() if self.to_screen(r).collidepoint(pos)), None)

    @override
    def handle_event(self, e):
        """Pan by dragging with the mouse or scrolling the wheel."""
        if super().handle_event(e):
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and VIEW.collidepoint(e.pos):
            self.dragging = True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            self.pan_by(-e.rel[0], -e.rel[1])
        elif e.type == pygame.MOUSEWHEEL:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                self.pan_by(-e.y * 80, 0)
            else:
                self.pan_by(e.x * 80, -e.y * 80)

    @override
    def update(self, dt):
        """Animate the tanks and pan with the arrow or WASD keys."""
        self.t += dt
        keys = pygame.key.get_pressed()
        for key, (dx, dy) in PAN_KEYS.items():
            if keys[key]:
                self.pan_by(dx * PAN_SPEED * dt, dy * PAN_SPEED * dt)

    @override
    def draw(self, surf):
        super().draw(surf)
        ui.text(
            surf,
            "Drag, scroll or use the arrow keys to explore. Hover a tank to trace its path.",
            24,
            (C.SCREEN_W // 2, 108),
            anchor="center",
        )
        surf.set_clip(VIEW)
        ui.panel(surf, VIEW, (225, 225, 230), alpha=170, radius=0)
        focus = self.hovered()
        self.draw_edges(surf, focus)
        for name, rect in CARDS.items():
            screen = self.to_screen(rect)
            if screen.colliderect(VIEW):
                self.draw_card(surf, screen, name, name == focus)
        surf.set_clip(None)
        self.draw_minimap(surf)

    def draw_edges(self, surf, focus):
        """Draw a line from every tank to each tank it evolves into, the focused ones on top."""
        lit = [e for e in EDGES if focus in e]
        for parent, child in [e for e in EDGES if focus not in e] + lit:
            a = self.to_screen(CARDS[parent]).midright
            b = self.to_screen(CARDS[child]).midleft
            if max(a[0], b[0]) < VIEW.left or min(a[0], b[0]) > VIEW.right:
                continue
            on = (parent, child) in lit
            pygame.draw.lines(
                surf, HIGHLIGHT if on else EDGE_COLOR, False, curve(a, b), 4 if on else 2
            )

    def draw_card(self, surf, rect, name, focused):
        """Draw one tank card: body, name, level and unlock route."""
        t = TANKS[name]
        owned = meta.tank_unlocked(self.profile, name)
        ui.panel(surf, rect, alpha=240)
        if focused:
            pygame.draw.rect(surf, HIGHLIGHT, rect, 3, border_radius=10)
        pose = R.Pose(rect.x + 38, rect.centery, 20, -math.pi / 4)
        color = C.PLAYER_COLOR if owned else (150, 150, 150)
        R.draw_tank_body(surf, t, pose, color, spin=self.t * 3)
        x = rect.x + 72
        ui.text(surf, name, 26, (x, rect.y + 14))
        ui.text(
            surf, f"Lv {t['level']}", 20, (rect.right - 10, rect.y + 16), C.XP_YELLOW, "topright"
        )
        route = meta.how_to_get(name)
        ui.text(surf, route, 17, (x, rect.y + 50), C.HP_GREEN if owned else C.GEM_COLOR)
        if ANY in t["parents"]:
            ui.text(surf, "any Lv 15+ >", 18, (rect.x - 8, rect.centery), EDGE_COLOR, "midright")

    def draw_minimap(self, surf):
        """Draw a small overview of the map with the visible area outlined."""
        scale = 200 / MAP_W
        box = pygame.Rect(0, 0, 200, round(MAP_H * scale)).move(
            C.SCREEN_W - 216, C.SCREEN_H - 16 - round(MAP_H * scale)
        )
        ui.panel(surf, box.inflate(8, 8), alpha=200, radius=6)
        for rect in CARDS.values():
            dot = pygame.Rect(
                box.x + rect.x * scale, box.y + rect.y * scale, CARD_W * scale, CARD_H * scale
            )
            pygame.draw.rect(surf, (150, 150, 160), dot)
        seen = pygame.Rect(
            box.x + self.cam.x * scale, box.y + self.cam.y * scale, VIEW.w * scale, VIEW.h * scale
        )
        pygame.draw.rect(surf, C.WHITE, seen.clip(box), 1)
