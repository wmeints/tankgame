import math
import random

import pygame

from .. import config as C
from .. import meta, ui
from ..data import progression as P
from .menu import BackScene

SEG_COLORS = [
    (241, 78, 84),
    (255, 232, 105),
    (118, 141, 252),
    (140, 255, 110),
    (252, 160, 80),
    (190, 120, 240),
    (90, 220, 255),
    (255, 215, 0),
]


class WheelScene(BackScene):
    title = "Prize Wheel"

    def __init__(self, game):
        super().__init__(game)
        self.angle = 0.0
        self.spinning = False
        self.spin_t = 0.0
        self.start = self.target = 0.0
        self.prize = None
        self.message = ""
        self.spin_btn = ui.Button(
            (C.SCREEN_W // 2 - 120, C.SCREEN_H - 110, 240, 64),
            "SPIN!",
            self.spin,
            size=40,
            color=(80, 200, 100),
        )

    def spin(self):
        if self.spinning or not meta.can_spin(self.profile):
            return
        meta.use_spin(self.profile)
        self.prize = meta.pick_prize()
        n = len(P.WHEEL_PRIZES)
        seg = math.tau / n
        # pointer is at the top (-pi/2); land the middle of the prize segment there
        land = -math.pi / 2 - (self.prize + 0.5) * seg + random.uniform(-0.35, 0.35) * seg
        self.start = self.angle
        base = self.angle - (self.angle % math.tau)
        self.target = base + math.tau * 6 + (land % math.tau)
        self.spin_t = 0.0
        self.spinning = True
        self.message = ""

    def handle_event(self, e):
        if super().handle_event(e):
            return
        if self.spin_btn.handle(e):
            self.game.sfx.play("click")

    def update(self, dt):
        if not self.spinning:
            return
        self.spin_t += dt / 4.0
        if self.spin_t >= 1:
            self.spin_t = 1
            self.spinning = False
            self.message = meta.apply_prize(self.profile, self.prize)
            self.game.save()
            self.game.sfx.play("evolve" if P.WHEEL_PRIZES[self.prize][1] == "tank" else "gem")
        ease = 1 - (1 - self.spin_t) ** 3
        self.angle = self.start + (self.target - self.start) * ease

    def draw(self, surf):
        super().draw(surf)
        prof = self.profile
        cx, cy, r = C.SCREEN_W // 2, 390, 240
        n = len(P.WHEEL_PRIZES)
        seg = math.tau / n
        for i, (label, _k, _v, _w) in enumerate(P.WHEEL_PRIZES):
            a0 = self.angle + i * seg
            pts = [(cx, cy)] + [
                (cx + math.cos(a0 + seg * k / 12) * r, cy + math.sin(a0 + seg * k / 12) * r)
                for k in range(13)
            ]
            pygame.draw.polygon(surf, SEG_COLORS[i % len(SEG_COLORS)], pts)
            pygame.draw.polygon(surf, (60, 60, 60), pts, 3)
            mid = a0 + seg / 2
            ui.text(
                surf,
                label,
                22,
                (cx + math.cos(mid) * r * 0.62, cy + math.sin(mid) * r * 0.62),
                anchor="center",
            )
        pygame.draw.circle(surf, (60, 60, 60), (cx, cy), 30)
        pygame.draw.polygon(
            surf, C.WHITE, [(cx - 18, cy - r - 30), (cx + 18, cy - r - 30), (cx, cy - r + 8)]
        )
        pygame.draw.polygon(
            surf,
            (60, 60, 60),
            [(cx - 18, cy - r - 30), (cx + 18, cy - r - 30), (cx, cy - r + 8)],
            3,
        )
        free = prof["last_free_spin"] != meta.today()
        info = (
            "Free daily spin available!"
            if free
            else f"Spins: {prof['spins']}  (free spin again tomorrow)"
        )
        ui.text(surf, info, 28, (cx, 100), anchor="center")
        self.spin_btn.enabled = meta.can_spin(prof) and not self.spinning
        self.spin_btn.draw(surf)
        if self.message:
            ui.text(surf, self.message, 40, (cx, C.SCREEN_H - 150), C.XP_YELLOW, anchor="center")
