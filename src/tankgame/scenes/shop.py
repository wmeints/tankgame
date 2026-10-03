import math

import pygame

from .. import config as C
from .. import meta, ui
from .. import render as R
from ..data import progression as P
from ..data.tanks import TANKS
from .menu import BackScene

TABS = ["Stat Caps", "Tanks", "Skins"]
SHOP_TANKS = [n for n, t in TANKS.items() if t["price"] > 0 or t["unlock"]]


class ShopScene(BackScene):
    title = "Shop"

    def __init__(self, game):
        super().__init__(game)
        self.tab = 0
        self.message = ""
        self.t = 0.0
        self.tab_buttons = [
            ui.Button(
                (C.SCREEN_W // 2 - 330 + i * 225, 100, 210, 46),
                name,
                lambda i=i: self.set_tab(i),
                size=28,
            )
            for i, name in enumerate(TABS)
        ]
        self.buttons = []
        self.build()

    def set_tab(self, i):
        self.tab = i
        self.message = ""
        self.build()

    def build(self):
        prof = self.profile
        self.buttons = []
        if self.tab == 0:
            for i, stat in enumerate(P.STATS):
                y = 190 + i * 62
                cost = meta.next_cap_cost(prof, stat)
                label = "MAXED" if cost is None else f"{cost:,}"
                b = ui.Button(
                    (C.SCREEN_W - 380, y, 220, 48),
                    label,
                    lambda s=stat: self.buy_cap(s),
                    size=28,
                    enabled=cost is not None and prof["gems"] >= cost,
                    color=(80, 200, 100),
                )
                self.buttons.append(b)
        elif self.tab == 1:
            for i, name in enumerate(SHOP_TANKS):
                card = self.tank_card(i)
                t = TANKS[name]
                owned = meta.tank_unlocked(prof, name)
                if owned:
                    label, enabled = "OWNED", False
                elif t["price"] > 0:
                    label, enabled = f"{t['price']:,}", prof["gems"] >= t["price"]
                else:
                    label, enabled = meta.lock_reason(prof, name), False
                self.buttons.append(
                    ui.Button(
                        (card.x + 14, card.bottom - 58, card.w - 28, 44),
                        label,
                        lambda n=name: self.buy_tank(n),
                        size=26,
                        enabled=enabled,
                        color=(80, 200, 100),
                    )
                )
        else:
            for i, (name, _col, price) in enumerate(P.SKINS):
                card = self.skin_card(i)
                if prof["skin"] == name:
                    label, enabled = "EQUIPPED", False
                elif name in prof["skins"]:
                    label, enabled = "Equip", True
                else:
                    label, enabled = f"{price:,}", prof["gems"] >= price
                self.buttons.append(
                    ui.Button(
                        (card.x + 12, card.bottom - 54, card.w - 24, 42),
                        label,
                        lambda n=name: self.skin(n),
                        size=26,
                        enabled=enabled,
                        color=(80, 200, 100),
                    )
                )

    def tank_card(self, i):
        col, row = i % 4, i // 4
        return pygame.Rect(C.SCREEN_W // 2 - 520 + col * 265, 180 + row * 300, 245, 280)

    def skin_card(self, i):
        col, row = i % 4, i // 4
        return pygame.Rect(C.SCREEN_W // 2 - 520 + col * 265, 190 + row * 270, 245, 250)

    def buy_cap(self, stat):
        if meta.buy_cap(self.profile, stat):
            self.message = (
                f"{P.STAT_NAMES[stat]} cap raised to {meta.stat_cap(self.profile, stat)}!"
            )
            self.game.sfx.play("gem")
            self.game.save()
        self.build()

    def buy_tank(self, name):
        if meta.buy_tank(self.profile, name):
            self.message = f"{name} unlocked! Evolve into it at level {TANKS[name]['level']}."
            self.game.sfx.play("evolve")
            self.game.save()
        self.build()

    def skin(self, name):
        prof = self.profile
        if name not in prof["skins"]:
            if not meta.buy_skin(prof, name):
                return
            self.game.sfx.play("gem")
        prof["skin"] = name
        self.game.save()
        self.build()

    def handle_event(self, e):
        if super().handle_event(e):
            return
        for b in self.tab_buttons + self.buttons:
            if b.handle(e):
                self.game.sfx.play("click")
                return

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        super().draw(surf)
        prof = self.profile
        for i, b in enumerate(self.tab_buttons):
            b.color = C.UI_ACCENT if i == self.tab else (120, 120, 140)
            b.draw(surf)
        if self.tab == 0:
            ui.text(
                surf,
                "Raise the max points you can put into each stat during a run.",
                24,
                (C.SCREEN_W // 2, 165),
                anchor="center",
            )
            for i, stat in enumerate(P.STATS):
                y = 190 + i * 62
                row = pygame.Rect(160, y - 4, C.SCREEN_W - 320, 56)
                ui.panel(surf, row, alpha=190)
                ui.text(surf, P.STAT_NAMES[stat], 28, (row.x + 16, row.y + 16))
                cap = meta.stat_cap(prof, stat)
                for k in range(P.MAX_CAPS[stat]):
                    r = pygame.Rect(row.x + 220 + k * 34, row.y + 14, 30, 28)
                    c = P.STAT_COLORS[stat] if k < cap else (40, 40, 45)
                    pygame.draw.rect(surf, c, r, border_radius=4)
                ui.text(surf, f"{cap}/{P.MAX_CAPS[stat]}", 26, (row.x + 670, row.y + 16))
        elif self.tab == 1:
            for i, name in enumerate(SHOP_TANKS):
                t = TANKS[name]
                card = self.tank_card(i)
                ui.panel(surf, card, alpha=200)
                owned = meta.tank_unlocked(prof, name)
                R.draw_tank_body(
                    surf,
                    t,
                    R.Pose(card.centerx, card.y + 80, 30, -math.pi / 4 + math.sin(self.t) * 0.3),
                    C.PLAYER_COLOR if owned else (150, 150, 150),
                    spin=self.t * 3,
                )
                ui.text(surf, name, 28, (card.centerx, card.y + 150), anchor="center")
                ui.text(
                    surf, f"Level {t['level']}", 22, (card.centerx, card.y + 176), anchor="center"
                )
                ui.text(
                    surf,
                    t["desc"],
                    16,
                    (card.centerx, card.y + 200),
                    (220, 220, 220),
                    anchor="center",
                )
        else:
            for i, (name, col, _price) in enumerate(P.SKINS):
                card = self.skin_card(i)
                ui.panel(surf, card, alpha=200)
                color = col or R.rainbow(self.t)
                pose = R.Pose(card.centerx, card.y + 80, 34, -math.pi / 4)
                R.draw_tank_body(surf, TANKS["Basic"], pose, color)
                ui.text(surf, name, 30, (card.centerx, card.y + 160), anchor="center")
        for b in self.buttons:
            b.draw(surf)
        if self.message:
            ui.text(
                surf,
                self.message,
                30,
                (C.SCREEN_W // 2, C.SCREEN_H - 30),
                C.XP_YELLOW,
                anchor="center",
            )
