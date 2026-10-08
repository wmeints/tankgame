"""Tank index scene: every tank, where it evolves from and how to get it."""

import math
from typing import override

import pygame

from .. import config as C
from .. import meta, ui
from .. import render as R
from ..data.tanks import ANY, TANKS
from .menu import BackScene

COLS = 3
CARD_W, CARD_H, GAP = 380, 108, 14
VIEW = pygame.Rect(0, 140, C.SCREEN_W, C.SCREEN_H - 150)
LEFT = (C.SCREEN_W - COLS * CARD_W - (COLS - 1) * GAP) // 2
ORDER = sorted(TANKS, key=lambda n: (TANKS[n]["level"], n))
ROWS = math.ceil(len(ORDER) / COLS)
MAX_SCROLL = max(0, ROWS * (CARD_H + GAP) - GAP - VIEW.h)
SCROLL_KEYS = {
    pygame.K_UP: -60,
    pygame.K_DOWN: 60,
    pygame.K_PAGEUP: -VIEW.h,
    pygame.K_PAGEDOWN: VIEW.h,
}


def evolves_from(name):
    """Return the parents of a tank as display text."""
    parents = TANKS[name]["parents"]
    if not parents:
        return "-"
    return ", ".join("any level 15+ tank" if p == ANY else p for p in parents)


class TankIndexScene(BackScene):
    """Scrollable list of every tank with its level, parents and how to unlock it."""

    title = "Tank Index"

    def __init__(self, game):
        super().__init__(game)
        self.scroll = 0
        self.t = 0.0

    def scroll_by(self, dy):
        """Scroll the list by `dy` pixels, clamped to its length."""
        self.scroll = min(MAX_SCROLL, max(0, self.scroll + dy))

    def card(self, i):
        """Return the screen rect of the `i`-th tank card at the current scroll."""
        col, row = i % COLS, i // COLS
        y = VIEW.y + row * (CARD_H + GAP) - self.scroll
        return pygame.Rect(LEFT + col * (CARD_W + GAP), y, CARD_W, CARD_H)

    @override
    def handle_event(self, e):
        """Scroll with the mouse wheel or arrow and page keys."""
        if super().handle_event(e):
            return
        if e.type == pygame.MOUSEWHEEL:
            self.scroll_by(-e.y * 60)
        elif e.type == pygame.KEYDOWN and e.key in SCROLL_KEYS:
            self.scroll_by(SCROLL_KEYS[e.key])

    @override
    def update(self, dt):
        self.t += dt

    @override
    def draw(self, surf):
        super().draw(surf)
        ui.text(
            surf,
            "Every tank, where it evolves from and how to get it. Scroll to see more.",
            24,
            (C.SCREEN_W // 2, 108),
            anchor="center",
        )
        surf.set_clip(VIEW)
        for i, name in enumerate(ORDER):
            rect = self.card(i)
            if rect.colliderect(VIEW):
                self.draw_card(surf, rect, name)
        surf.set_clip(None)
        if MAX_SCROLL:
            track = pygame.Rect(C.SCREEN_W - 30, VIEW.y, 8, VIEW.h)
            thumb_h = track.h * VIEW.h // (VIEW.h + MAX_SCROLL)
            thumb_y = track.y + (track.h - thumb_h) * self.scroll // MAX_SCROLL
            pygame.draw.rect(surf, (40, 40, 45), track, border_radius=4)
            pygame.draw.rect(surf, C.WHITE, (track.x, thumb_y, 8, thumb_h), border_radius=4)

    def draw_card(self, surf, rect, name):
        """Draw one tank card: body, name, level, parents and unlock route."""
        t = TANKS[name]
        owned = meta.tank_unlocked(self.profile, name)
        ui.panel(surf, rect, alpha=235)
        pose = R.Pose(rect.x + 50, rect.centery, 24, -math.pi / 4)
        color = C.PLAYER_COLOR if owned else (150, 150, 150)
        R.draw_tank_body(surf, t, pose, color, spin=self.t * 3)
        x = rect.x + 100
        ui.text(surf, name, 28, (x, rect.y + 12))
        ui.text(
            surf, f"Lv {t['level']}", 24, (rect.right - 12, rect.y + 14), C.XP_YELLOW, "topright"
        )
        ui.text(surf, f"From: {evolves_from(name)}", 18, (x, rect.y + 46), (220, 220, 220))
        ui.text(
            surf,
            meta.how_to_get(name),
            18,
            (x, rect.y + 72),
            C.HP_GREEN if owned else C.GEM_COLOR,
        )
