import math

import pygame

from .. import config as C
from .. import meta
from .. import render as R
from .. import ui
from ..data import progression as P
from ..hud import Hud
from ..world import World
from . import Scene

STAT_KEYS = {pygame.K_1 + i: s for i, s in enumerate(P.STATS)}


class ArenaScene(Scene):
    def __init__(self, game, autoplay=False):
        super().__init__(game)
        meta.ensure_quests(self.profile)
        self.world = World(self.profile, sfx=game.sfx, autoplay=autoplay)
        self.cam = R.Camera()
        self.cam.x, self.cam.y = self.world.player.x, self.world.player.y
        self.hud = Hud(self)
        self.autofire = False
        self.mouse_fire = False
        self.user_zoom = 1.0
        self.paused = False
        self.finished = False
        self.end_msgs = []
        self.buttons = []

    # --- input ----------------------------------------------------------
    def handle_event(self, e):
        w = self.world
        if self.finished or self.paused:
            for b in self.buttons:
                if b.handle(e):
                    self.game.sfx.play("click")
                    return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and self.paused:
                self.paused = False
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE) and self.finished:
                self.play_again()
            return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.paused = True
                self.buttons = [
                    ui.Button((C.SCREEN_W // 2 - 140, 360, 280, 56), "Resume", self.resume),
                    ui.Button((C.SCREEN_W // 2 - 140, 436, 280, 56), "Leave Game",
                              self.leave, color=(200, 90, 90)),
                ]
            elif e.key == pygame.K_e:
                self.hud.stats_open = not self.hud.stats_open
            elif e.key == pygame.K_q:
                self.hud.evo_open = not self.hud.evo_open
            elif e.key == pygame.K_f:
                self.autofire = not self.autofire
            elif e.key == pygame.K_r:
                w.rebirth()
            elif e.key in STAT_KEYS:
                if w.player.upgrade(STAT_KEYS[e.key]):
                    w.sfx("click")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if not self.hud.handle_click(e.pos):
                self.mouse_fire = True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.mouse_fire = False
        elif e.type == pygame.MOUSEWHEEL:
            self.user_zoom = min(1.3, max(0.6, self.user_zoom + e.y * 0.05))

    def resume(self):
        self.paused = False

    def leave(self):
        self.paused = False
        self.world.dead = True
        self.world.killer_name = ""
        self.finish()
        from .menu import MenuScene
        self.game.goto(MenuScene(self.game))

    def play_again(self):
        self.game.goto(ArenaScene(self.game))

    def to_menu(self):
        from .menu import MenuScene
        self.game.goto(MenuScene(self.game))

    # --- update ---------------------------------------------------------
    def update(self, dt):
        if self.paused:
            return
        w = self.world
        p = w.player
        if not w.dead and not p.brain:
            keys = pygame.key.get_pressed()
            p.move_x = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
            p.move_y = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
            mx, my = pygame.mouse.get_pos()
            wx, wy = self.cam.to_world(mx, my)
            p.angle = math.atan2(wy - p.y, wx - p.x)
            p.firing = self.autofire or (self.mouse_fire and pygame.mouse.get_pressed()[0])
        elif w.dead:
            p.firing = False
            p.move_x = p.move_y = 0
        w.update(dt)
        if w.dead and not self.finished:
            self.finish()
        # camera
        k = min(1.0, 6 * dt)
        self.cam.x += (p.x - self.cam.x) * k
        self.cam.y += (p.y - self.cam.y) * k
        fov = p.tdef["fov"] * (1 + 0.0025 * (p.level - 1))
        target_zoom = self.user_zoom / fov
        self.cam.zoom += (target_zoom - self.cam.zoom) * min(1.0, 3 * dt)

    def finish(self):
        if self.finished:
            return
        self.finished = True
        w = self.world
        p = w.player
        self.end_msgs = meta.record_run(self.profile, p.score, p.level, w.run_kills)
        self.game.save()
        cx = C.SCREEN_W // 2
        self.buttons = [
            ui.Button((cx - 290, 600, 270, 60), "Play Again", self.play_again),
            ui.Button((cx + 20, 600, 270, 60), "Main Menu", self.to_menu, color=(120, 120, 140)),
        ]

    # --- draw -----------------------------------------------------------
    def draw(self, surf):
        w = self.world
        cam = self.cam
        R.draw_background(surf, cam)
        for s in w.shapes:
            if cam.visible(s.x, s.y, s.radius * 1.2):
                R.draw_shape(surf, cam, s)
        for b in w.bullets:
            if cam.visible(b.x, b.y, b.radius * 2):
                col = w.player.color if b.owner.is_player else C.ENEMY_COLOR
                R.draw_bullet(surf, cam, b, col)
        for beam in w.beams:
            f = beam.life / beam.max_life
            x1, y1 = cam.to_screen(beam.x1, beam.y1)
            x2, y2 = cam.to_screen(beam.x2, beam.y2)
            width = max(2, int(beam.width * cam.zoom * f))
            pygame.draw.line(surf, beam.color, (x1, y1), (x2, y2), width)
            pygame.draw.line(surf, C.WHITE, (x1, y1), (x2, y2), max(1, width // 3))
        labels = []
        for t in w.tanks:
            if not t.alive or not cam.visible(t.x, t.y, t.radius * 3):
                continue
            col = t.color
            sx, sy, r = R.draw_tank(surf, cam, t, col, w.time)
            if t.alpha > 0.3:
                labels.append((t, sx, sy, r))
        for ring in w.rings:
            f = ring.life / ring.max_life
            sx, sy = cam.to_screen(ring.x, ring.y)
            rad = ring.radius * cam.zoom * (1.5 - f * 0.5)
            pygame.draw.circle(surf, ring.color, (sx, sy), max(1, int(rad)), max(1, int(6 * f)))
        for t, sx, sy, r in labels:
            if not t.is_player:
                ui.text(surf, t.name, 18, (sx, sy - r - 18), anchor="center")
                ui.text(surf, f"Lvl {t.level} {t.tank_name}", 14, (sx, sy - r - 4), (230, 230, 230),
                        anchor="center")
            R.hp_bar(surf, sx, sy + r + 12, r * 2, t.hp / t.max_hp)
        if not self.finished:
            self.hud.draw(surf)
        if self.paused:
            self.draw_overlay(surf, "Paused")
        elif self.finished:
            self.draw_death(surf)

    def draw_overlay(self, surf, title):
        shade = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 140))
        surf.blit(shade, (0, 0))
        ui.text(surf, title, 72, (C.SCREEN_W // 2, 260), anchor="center")
        for b in self.buttons:
            b.draw(surf)

    def draw_death(self, surf):
        w = self.world
        p = w.player
        shade = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        surf.blit(shade, (0, 0))
        cx = C.SCREEN_W // 2
        if w.rebirthed:
            ui.text(surf, "REBIRTH!", 80, (cx, 150), C.XP_YELLOW, anchor="center")
            ui.text(surf, f"Rebirths: {self.profile['rebirths']}  (+5% XP each)", 30, (cx, 205),
                    anchor="center")
        else:
            ui.text(surf, "You were destroyed", 64, (cx, 150), anchor="center")
            if w.killer_name:
                ui.text(surf, f"by {w.killer_name}", 34, (cx, 200), C.ENEMY_COLOR, anchor="center")
        R.draw_tank_body(surf, p.tdef, cx, 300, 36, -math.pi / 4, p.color, spin=w.time * 3)
        lines = [f"Score: {int(p.score):,}", f"Level {p.level} {p.tank_name}",
                 f"Tanks destroyed: {w.run_kills}"]
        for i, line in enumerate(lines):
            ui.text(surf, line, 34, (cx, 380 + i * 38), anchor="center")
        y = 380 + len(lines) * 38
        ui.gems_label(surf, w.run_gems, (cx, y + 10), 30, anchor="midtop")
        for i, m in enumerate(self.end_msgs):
            ui.text(surf, m, 26, (cx, y + 50 + i * 28), C.GEM_COLOR, anchor="center")
        for b in self.buttons:
            b.draw(surf)
