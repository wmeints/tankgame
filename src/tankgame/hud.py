"""In-game HUD: score/level bars, stats panel (E), evolution picker (Q),
leaderboard, minimap, toasts."""

import math

import pygame

from . import config as C
from . import meta, ui
from .data import progression as P
from .render import Pose, draw_tank_body


class Hud:
    def __init__(self, scene):
        self.scene = scene
        self.stats_open = False
        self.evo_open = False
        self.stat_buttons = {}  # stat -> rect
        self.evo_cards = []  # (rect, tank def, unlocked)

    @property
    def world(self):
        return self.scene.world

    # --- input ----------------------------------------------------------
    def handle_click(self, pos) -> bool:
        """Returns True if the click was used by the HUD."""
        if self.stats_visible() and self._click_stats(pos):
            return True
        return self.evo_open and self._click_evolutions(pos)

    def _click_stats(self, pos) -> bool:
        w = self.world
        for stat, rect in self.stat_buttons.items():
            if rect.collidepoint(pos):
                if w.player.upgrade(stat):
                    w.sfx("click")
                return True
        return bool(self.stats_rect().collidepoint(pos))

    def _click_evolutions(self, pos) -> bool:
        for rect, tdef, unlocked in self.evo_cards:
            if rect.collidepoint(pos):
                self._pick_evolution(tdef["name"], unlocked)
                return True
        return bool(self.evo_rect().collidepoint(pos))

    def _pick_evolution(self, name, unlocked) -> None:
        w = self.world
        if unlocked:
            w.player_evolve(name)
            self.evo_open = False
        else:
            reason = meta.lock_reason(w.profile, name)
            w.toast(f"{name} is locked ({reason}). Unlock it in the Shop!", C.ENEMY_COLOR)

    # --- layout ---------------------------------------------------------
    def stats_visible(self):
        return self.stats_open or self.world.player.unspent > 0

    def stats_rect(self):
        return pygame.Rect(12, C.SCREEN_H - 12 - 8 * 30 - 44, 300, 8 * 30 + 44)

    def evo_rect(self):
        n = max(1, len(self.world.evolution_choices()))
        cols = min(4, n)
        rows = math.ceil(n / 4)
        return pygame.Rect(12, 60, cols * 118 + 12, rows * 128 + 46)

    # --- drawing --------------------------------------------------------
    def draw(self, surf):
        w = self.world
        p = w.player
        self.draw_bars(surf, p)
        if self.stats_visible():
            self.draw_stats(surf, p)
        opts = w.evolution_choices()
        if opts and not self.evo_open and not w.dead:
            pulse = 0.5 + 0.5 * math.sin(w.time * 6)
            col = tuple(int(c * (0.7 + 0.3 * pulse)) for c in C.XP_YELLOW)
            ui.text(surf, "Press Q to evolve!", 34, (C.SCREEN_W // 2, 80), col, anchor="center")
        if self.evo_open:
            self.draw_evolutions(surf, opts)
        self.draw_leaderboard(surf)
        self.draw_minimap(surf, p)
        self.draw_top_left(surf)
        for i, (msg, _ttl, col) in enumerate(reversed(w.toasts)):
            ui.text(surf, msg, 28, (C.SCREEN_W // 2, 120 + i * 30), col, anchor="center")
        if p.level >= P.REBIRTH_LEVEL and not w.dead:
            ui.text(
                surf,
                "MAX LEVEL - Press R to Rebirth",
                30,
                (C.SCREEN_W // 2, C.SCREEN_H - 120),
                C.XP_YELLOW,
                anchor="center",
            )
        if self.scene.autofire:
            ui.text(
                surf, "Auto Fire: ON (F)", 22, (C.SCREEN_W // 2, C.SCREEN_H - 92), anchor="center"
            )
        if p.immune > 0 and not w.dead:
            ui.text(
                surf,
                f"Spawn protection {p.immune:.0f}s",
                24,
                (C.SCREEN_W // 2, C.SCREEN_H - 150),
                anchor="center",
            )

    def draw_top_left(self, surf):
        w = self.world
        if self.evo_open:
            return
        ui.gems_label(surf, w.profile["gems"], (12, 14))
        r = meta.rank(w.profile)
        ui.text(
            surf,
            f"{P.rank_name(r)}  |  {w.difficulty.title()}  |  Kills: {w.run_kills}",
            22,
            (14, 44),
            (220, 220, 220),
        )

    def draw_bars(self, surf, p):
        cx = C.SCREEN_W // 2
        score_rect = pygame.Rect(0, 0, 360, 24)
        score_rect.midbottom = (cx, C.SCREEN_H - 46)
        best = max([t.score for t in self.world.tanks if t.alive] + [1])
        ui.bar(surf, score_rect, p.score / best, C.HP_GREEN)
        ui.text(surf, f"Score: {int(p.score):,}", 22, score_rect.center, anchor="center")
        lvl_rect = pygame.Rect(0, 0, 480, 28)
        lvl_rect.midbottom = (cx, C.SCREEN_H - 12)
        if p.level >= P.MAX_LEVEL:
            frac = 1.0
        else:
            lo, hi = P.total_xp_for_level(p.level), P.total_xp_for_level(p.level + 1)
            frac = (p.score - lo) / (hi - lo)
        ui.bar(surf, lvl_rect, frac, C.XP_YELLOW)
        ui.text(surf, f"Lvl {p.level} {p.tank_name}", 24, lvl_rect.center, anchor="center")

    def draw_stats(self, surf, p):
        rect = self.stats_rect()
        ui.panel(surf, rect, alpha=170)
        title = f"Upgrades  ({p.unspent} points)" if p.unspent else "Upgrades"
        ui.text(surf, title, 26, (rect.x + 12, rect.y + 10), C.XP_YELLOW if p.unspent else C.TEXT)
        self.stat_buttons = {}
        for i, stat in enumerate(P.STATS):
            y = rect.y + 40 + i * 30
            col = P.STAT_COLORS[stat]
            maxc = P.MAX_CAPS[stat]
            seg_w = 170 / maxc
            for k in range(maxc):
                r = pygame.Rect(rect.x + 12 + k * seg_w, y, seg_w - 2, 22)
                if k < p.points[stat]:
                    c = col
                elif k < p.caps[stat]:
                    c = (70, 70, 80)
                else:
                    c = (35, 35, 40)  # locked: buy in the shop
                pygame.draw.rect(surf, c, r, border_radius=3)
            ui.text(surf, f"{P.STAT_NAMES[stat]}", 18, (rect.x + 16, y + 4))
            ui.text(surf, f"[{i + 1}]", 18, (rect.x + 192, y + 4), (200, 200, 200))
            btn = pygame.Rect(rect.x + 236, y, 50, 22)
            if p.can_upgrade(stat):
                pygame.draw.rect(surf, col, btn, border_radius=5)
                ui.text(surf, "+", 26, btn.center, anchor="center")
            else:
                pygame.draw.rect(surf, (80, 80, 80), btn, border_radius=5)
                ui.text(surf, f"{p.points[stat]}/{p.caps[stat]}", 18, btn.center, anchor="center")
            self.stat_buttons[stat] = btn

    def draw_evolutions(self, surf, opts):
        w = self.world
        rect = self.evo_rect()
        ui.panel(surf, rect, alpha=200)
        if not opts:
            ui.text(surf, "No evolutions right now", 26, (rect.x + 12, rect.y + 12))
            nxt = [lv for lv in (15, 30, 42, 60, 80, 90, 105, 130, 150) if lv > w.player.level]
            if nxt:
                ui.text(surf, f"Next at level {nxt[0]}", 22, (rect.x + 12, rect.y + 40))
            self.evo_cards = []
            return
        ui.text(
            surf, "Choose your evolution (Q to close)", 24, (rect.x + 12, rect.y + 12), C.XP_YELLOW
        )
        self.evo_cards = []
        mouse = pygame.mouse.get_pos()
        for i, t in enumerate(opts):
            col, row = i % 4, i // 4
            card = pygame.Rect(rect.x + 12 + col * 118, rect.y + 42 + row * 128, 108, 118)
            unlocked = meta.tank_unlocked(w.profile, t["name"])
            base = (90, 140, 200) if unlocked else (90, 90, 95)
            if card.collidepoint(mouse) and unlocked:
                base = tuple(min(255, c + 30) for c in base)
            pygame.draw.rect(surf, base, card, border_radius=8)
            draw_tank_body(
                surf,
                t,
                Pose(card.centerx, card.y + 48, 16, -math.pi / 4),
                w.player.color if unlocked else (150, 150, 150),
                spin=w.time * 3,
            )
            ui.text(
                surf,
                t["name"],
                18 if len(t["name"]) < 12 else 16,
                (card.centerx, card.bottom - 26),
                anchor="center",
            )
            if unlocked:
                ui.text(
                    surf, f"Lvl {t['level']}", 16, (card.centerx, card.bottom - 10), anchor="center"
                )
            else:
                ui.text(
                    surf,
                    "LOCKED " + meta.lock_reason(w.profile, t["name"]),
                    14,
                    (card.centerx, card.bottom - 10),
                    C.ENEMY_COLOR,
                    anchor="center",
                )
            self.evo_cards.append((card, t, unlocked))

    def draw_leaderboard(self, surf):
        w = self.world
        tanks = sorted([t for t in w.tanks if t.alive], key=lambda t: -t.score)[:10]
        rect = pygame.Rect(C.SCREEN_W - 262, 12, 250, 36 + len(tanks) * 24)
        ui.panel(surf, rect, alpha=140)
        ui.text(surf, "Leaderboard", 26, (rect.centerx, rect.y + 16), anchor="center")
        top = tanks[0].score if tanks else 1
        for i, t in enumerate(tanks):
            y = rect.y + 34 + i * 24
            r = pygame.Rect(rect.x + 8, y, 234, 20)
            col = w.player.color if t.is_player else C.ENEMY_COLOR
            ui.bar(surf, r, t.score / max(1, top), col, back=(50, 50, 50), radius=6)
            name = t.name if len(t.name) < 16 else t.name[:15] + "."
            ui.text(surf, f"{name} - {_short(t.score)}", 16, r.center, anchor="center")

    def draw_minimap(self, surf, p):
        size = 150
        rect = pygame.Rect(C.SCREEN_W - size - 12, C.SCREEN_H - size - 12, size, size)
        ui.panel(surf, rect, color=(150, 150, 150), alpha=170, radius=4)
        s = size / C.ARENA_SIZE
        pygame.draw.circle(surf, (140, 135, 160), rect.center, C.NEST_RADIUS * s)
        pygame.draw.rect(surf, (90, 90, 90), rect, 2, border_radius=4)
        px, py = rect.x + p.x * s, rect.y + p.y * s
        a = p.angle
        pts = [
            (px + math.cos(a) * 7, py + math.sin(a) * 7),
            (px + math.cos(a + 2.5) * 5, py + math.sin(a + 2.5) * 5),
            (px + math.cos(a - 2.5) * 5, py + math.sin(a - 2.5) * 5),
        ]
        pygame.draw.polygon(surf, (30, 30, 30), pts)


def _short(n):
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}m"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)
