"""Main menu, the shared back-button scene, and the quests and codes screens."""

import math
import random
from typing import override

import pygame

from .. import config as C
from .. import meta, ui
from .. import render as R
from ..data import progression as P
from ..data.tanks import TANKS
from . import Scene

DIFFS = ["easy", "normal", "hard"]


class Backdrop:
    """Slowly drifting shapes behind the menus."""

    def __init__(self):
        self.items = [
            [
                random.uniform(0, C.SCREEN_W),
                random.uniform(0, C.SCREEN_H),
                random.choice((3, 4, 5)),
                random.uniform(0, math.tau),
                random.uniform(-12, 12),
                random.uniform(-12, 12),
            ]
            for _ in range(26)
        ]
        self.t = 0.0

    def draw(self, surf, dt=1 / 60):
        """Advance the shapes by `dt` seconds and draw the grid and shapes."""
        self.t += dt
        surf.fill(C.BG)
        for x in range(0, C.SCREEN_W, 50):
            pygame.draw.line(surf, C.BG_GRID, (x, 0), (x, C.SCREEN_H))
        for y in range(0, C.SCREEN_H, 50):
            pygame.draw.line(surf, C.BG_GRID, (0, y), (C.SCREEN_W, y))
        colors = {3: C.TRIANGLE_COLOR, 4: C.SQUARE_COLOR, 5: C.PENTAGON_COLOR}
        for it in self.items:
            it[0] = (it[0] + it[4] * dt) % C.SCREEN_W
            it[1] = (it[1] + it[5] * dt) % C.SCREEN_H
            it[3] += 0.3 * dt
            n = int(it[2])
            pts = [
                (
                    it[0] + math.cos(it[3] + i * math.tau / n) * 26,
                    it[1] + math.sin(it[3] + i * math.tau / n) * 26,
                )
                for i in range(n)
            ]
            R.poly(surf, colors[n], pts, 3)


_backdrop = None


def backdrop():
    """Return the shared backdrop, so it keeps drifting across menu screens."""
    global _backdrop
    if _backdrop is None:
        _backdrop = Backdrop()
    return _backdrop


class MenuScene(Scene):
    """Title screen with the player card, controls and menu buttons."""

    def __init__(self, game):
        super().__init__(game)
        meta.ensure_quests(self.profile)
        self.t = 0.0
        cx = C.SCREEN_W // 2
        x = cx - 160
        self.buttons = [
            ui.Button((x, 300, 320, 64), "PLAY", self.play, size=44, color=(80, 200, 100)),
            ui.Button((x, 380, 320, 50), "Shop", self.shop),
            ui.Button((x, 440, 320, 50), "Quests", self.quests),
            ui.Button((x, 500, 320, 50), "Tank Index", self.index, color=(220, 150, 60)),
            ui.Button((x, 560, 320, 50), "Codes", self.codes, color=(110, 110, 220)),
            ui.Button((x, 620, 155, 46), "", self.cycle_diff, size=26, color=(120, 120, 140)),
            ui.Button(
                (x + 165, 620, 155, 46), "Quit", self.game.quit, size=26, color=(200, 90, 90)
            ),
        ]
        self.diff_btn = self.buttons[5]

    def play(self):
        """Start a new arena run."""
        from .arena import ArenaScene

        self.game.goto(ArenaScene(self.game))

    def shop(self):
        """Open the shop."""
        from .shop import ShopScene

        self.game.goto(ShopScene(self.game))

    def quests(self):
        """Open the quest list."""
        self.game.goto(QuestScene(self.game))

    def index(self):
        """Open the tank index."""
        from .index import TankIndexScene

        self.game.goto(TankIndexScene(self.game))

    def codes(self):
        """Open the code redemption screen."""
        self.game.goto(CodesScene(self.game))

    def cycle_diff(self):
        """Switch to the next bot difficulty and save it."""
        i = DIFFS.index(self.profile["difficulty"])
        self.profile["difficulty"] = DIFFS[(i + 1) % 3]
        self.game.save()

    @override
    def handle_event(self, e):
        """Press a menu button, or start a run on Enter or Space."""
        for b in self.buttons:
            if b.handle(e):
                self.game.sfx.play("click")
                return
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.play()

    @override
    def update(self, dt):
        self.t += dt

    @override
    def draw(self, surf):
        backdrop().draw(surf)
        prof = self.profile
        cx = C.SCREEN_W // 2
        bob = math.sin(self.t * 2) * 6
        ui.text(surf, "TANK GAME!", 110, (cx, 120 + bob), C.WHITE, anchor="center")
        ui.plain_text(surf, "offline edition", 30, (cx, 185), (60, 60, 70), anchor="center")
        R.draw_tank_body(surf, TANKS["Basic"], R.Pose(cx - 450, 140, 40, self.t), C.PLAYER_COLOR)
        R.draw_tank_body(
            surf, TANKS["Orchestra"], R.Pose(cx + 450, 140, 40, -self.t * 0.7), C.ENEMY_COLOR
        )

        # player card
        card = pygame.Rect(40, 300, 330, 300)
        ui.panel(surf, card, alpha=190)
        ui.gems_label(surf, prof["gems"], (card.x + 16, card.y + 16), 40)
        rank = meta.rank(prof)
        ui.text(surf, f"Rank: {P.rank_name(rank)}", 30, (card.x + 16, card.y + 70))
        if rank < P.RANK_COUNT:
            lo, hi = P.rank_threshold(rank), P.rank_threshold(rank + 1)
            ui.bar(
                surf,
                pygame.Rect(card.x + 16, card.y + 102, card.w - 32, 16),
                (prof["total_score"] - lo) / (hi - lo),
                C.XP_YELLOW,
            )
        ui.text(surf, f"Best score: {prof['best_score']:,}", 24, (card.x + 16, card.y + 132))
        ui.text(surf, f"Best level: {prof['best_level']}", 24, (card.x + 16, card.y + 160))
        ui.text(surf, f"Total kills: {prof['total_kills']:,}", 24, (card.x + 16, card.y + 188))
        ui.text(surf, f"Rebirths: {prof['rebirths']}", 24, (card.x + 16, card.y + 216))
        if prof["pending_xp"]:
            ui.text(
                surf,
                f"Head start ready: {prof['pending_xp']:,} XP",
                22,
                (card.x + 16, card.y + 250),
                C.XP_YELLOW,
            )

        # controls card
        help_rect = pygame.Rect(C.SCREEN_W - 370, 300, 330, 300)
        ui.panel(surf, help_rect, alpha=190)
        lines = [
            "WASD - move",
            "Mouse - aim",
            "Left click - shoot",
            "F - auto fire",
            "E - upgrades (1-8)",
            "Q - evolve",
            "Scroll - zoom",
            "Esc - pause",
            "F11 - fullscreen",
        ]
        ui.text(surf, "Controls", 30, (help_rect.x + 16, help_rect.y + 14))
        for i, line in enumerate(lines):
            ui.text(surf, line, 24, (help_rect.x + 16, help_rect.y + 52 + i * 26))

        self.diff_btn.label = prof["difficulty"].title()
        for b in self.buttons:
            b.draw(surf)


class BackScene(Scene):
    """Menu sub-screen with a title, a back button and the gem count."""

    title = ""

    def __init__(self, game):
        super().__init__(game)
        self.back = ui.Button(
            (24, 24, 140, 46), "< Back", self.go_back, color=(120, 120, 140), size=28
        )

    def go_back(self):
        """Save the profile and return to the main menu."""
        self.game.save()
        self.game.goto(MenuScene(self.game))

    @override
    def handle_event(self, e):
        """Handle the back button and Escape.

        Returns
        -------
        bool
            True when the event was consumed, so subclasses can skip it.
        """
        if self.back.handle(e):
            self.game.sfx.play("click")
            return True
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.go_back()
            return True
        return False

    @override
    def draw(self, surf):
        """Draw the backdrop, title, back button and gem count."""
        backdrop().draw(surf)
        ui.text(surf, self.title, 64, (C.SCREEN_W // 2, 50), anchor="center")
        self.back.draw(surf)
        ui.gems_label(surf, self.profile["gems"], (C.SCREEN_W - 220, 34), 34)


class QuestScene(BackScene):
    """List of daily, weekly and unique quests with their progress."""

    title = "Quests"

    @override
    def draw(self, surf):
        super().draw(surf)
        meta.ensure_quests(self.profile)
        y = 110
        last_kind = None
        for kind, e in meta.all_quest_entries(self.profile):
            _qid, text, _ev, target, _mode, reward = meta.QUEST_DEFS[e["id"]]
            if kind != last_kind:
                ui.text(
                    surf,
                    {
                        "Daily": "Daily quests (reset every day)",
                        "Weekly": "Weekly quests",
                        "Unique": "Unique quests (once only)",
                    }[kind],
                    30,
                    (140, y),
                )
                y += 38
                last_kind = kind
            row = pygame.Rect(140, y, C.SCREEN_W - 280, 50)
            ui.panel(surf, row, color=(50, 110, 60) if e["done"] else C.UI_PANEL, alpha=200)
            ui.text(surf, text, 26, (row.x + 14, row.y + 8))
            bar = pygame.Rect(row.x + 14, row.y + 32, 360, 10)
            ui.bar(surf, bar, e["progress"] / target, C.XP_YELLOW, radius=4)
            ui.text(surf, f"{int(e['progress']):,}/{target:,}", 18, (bar.right + 10, row.y + 28))
            rtxt = f"{reward:,} gems" if isinstance(reward, int) else f"Tank: {reward}"
            ui.text(
                surf,
                "DONE!" if e["done"] else rtxt,
                26,
                (row.right - 14, row.centery),
                C.HP_GREEN if e["done"] else C.GEM_COLOR,
                anchor="midright",
            )
            y += 58


class CodesScene(BackScene):
    """Text entry for redeeming codes."""

    title = "Codes"
    wants_text = True

    def __init__(self, game):
        super().__init__(game)
        self.entry = ""
        self.message = "Type a code and press Enter"
        self.redeem_btn = ui.Button(
            (C.SCREEN_W // 2 - 110, 400, 220, 56), "Redeem", self.redeem, color=(80, 200, 100)
        )

    def redeem(self):
        """Redeem the typed code, show the result and clear the entry."""
        self.message = meta.redeem_code(self.profile, self.entry)
        self.entry = ""
        self.game.save()
        self.game.sfx.play("gem")

    @override
    def handle_event(self, e):
        """Type, erase or submit the code, on top of the back-button handling."""
        if super().handle_event(e):
            return
        if self.redeem_btn.handle(e):
            return
        if e.type == pygame.TEXTINPUT:
            if len(self.entry) < 20:
                self.entry += e.text.upper()
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_BACKSPACE:
                self.entry = self.entry[:-1]
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.redeem()

    @override
    def draw(self, surf):
        super().draw(surf)
        cx = C.SCREEN_W // 2
        box = pygame.Rect(cx - 250, 300, 500, 70)
        pygame.draw.rect(surf, C.WHITE, box, border_radius=10)
        pygame.draw.rect(surf, C.UI_ACCENT, box, 4, border_radius=10)
        cursor = "|" if int(pygame.time.get_ticks() / 500) % 2 == 0 else ""
        ui.plain_text(surf, self.entry + cursor, 44, box.center, (40, 40, 40), anchor="center")
        self.redeem_btn.draw(surf)
        ui.text(surf, self.message, 32, (cx, 500), C.XP_YELLOW, anchor="center")
        ui.text(
            surf,
            f"Codes redeemed: {len(self.profile['redeemed_codes'])}",
            24,
            (cx, 560),
            anchor="center",
        )
        ui.plain_text(
            surf,
            "Codes come from the real Tank Game's code list.",
            22,
            (cx, 600),
            (60, 60, 70),
            anchor="center",
        )
