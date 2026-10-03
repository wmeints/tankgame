"""Tiny synthesized sound effects (no audio files needed)."""

import array
import math
import random

import pygame

RATE = 22050


def _tone(freq0, freq1, dur, vol=0.3, noise=0.0, decay=6.0):
    n = int(RATE * dur)
    buf = array.array("h")
    phase = 0.0
    for i in range(n):
        t = i / n
        f = freq0 + (freq1 - freq0) * t
        phase += math.tau * f / RATE
        v = math.sin(phase) * (1 - noise) + random.uniform(-1, 1) * noise
        env = math.exp(-decay * t) * min(1.0, i / 80)
        buf.append(int(v * env * vol * 32767))
    return buf.tobytes()


class Sfx:
    """Synthesized sound effects, silently disabled when no audio device is available."""

    def __init__(self):
        self.sounds = {}
        self.enabled = False
        try:
            pygame.mixer.init(RATE, -16, 1, 512)
            self.sounds = {
                "shoot": _tone(420, 180, 0.07, 0.12, noise=0.3, decay=8),
                "hit": _tone(200, 120, 0.05, 0.1, noise=0.5),
                "kill": _tone(300, 80, 0.25, 0.25, noise=0.6, decay=5),
                "levelup": _tone(500, 900, 0.18, 0.18, decay=3),
                "evolve": _tone(300, 1200, 0.45, 0.22, decay=2),
                "gem": _tone(1200, 1600, 0.1, 0.12, decay=4),
                "click": _tone(700, 600, 0.04, 0.12),
                "death": _tone(250, 40, 0.8, 0.3, noise=0.4, decay=3),
            }
            self.sounds = {k: pygame.mixer.Sound(buffer=v) for k, v in self.sounds.items()}
            self.enabled = True
        except pygame.error, NotImplementedError:
            self.sounds = {}
        self.cooldown = {}

    def play(self, name):
        """Play a named sound, skipping repeats within 40 ms of each other."""
        if not self.enabled or name is None:
            return
        now = pygame.time.get_ticks()
        if now - self.cooldown.get(name, 0) < 40:
            return
        self.cooldown[name] = now
        snd = self.sounds.get(name)
        if snd:
            snd.play()
