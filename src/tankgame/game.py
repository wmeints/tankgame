import copy
import os
import sys

import pygame

from . import config as C
from . import save as S
from .sfx import Sfx


class Game:
    def __init__(self, headless=False, profile=None):
        pygame.init()
        pygame.display.set_caption("Tank Game! (offline)")
        self.headless = headless
        try:
            self.screen = pygame.display.set_mode(
                (C.SCREEN_W, C.SCREEN_H), pygame.SCALED | pygame.RESIZABLE
            )
        except pygame.error:
            self.screen = pygame.display.set_mode((C.SCREEN_W, C.SCREEN_H))
        self.clock = pygame.time.Clock()
        self.sfx = Sfx() if not headless else _NoSfx()
        self.profile = profile if profile is not None else S.load()
        self.running = True
        self.scene = None

    def save(self):
        if not self.headless:
            S.save(self.profile)

    def goto(self, scene):
        pygame.key.stop_text_input()
        self.scene = scene
        if getattr(scene, "wants_text", False):
            pygame.key.start_text_input()

    def quit(self):
        self.running = False

    def run(self):
        from .scenes.menu import MenuScene

        self.goto(MenuScene(self))
        acc = 0.0
        while self.running:
            frame = self.clock.tick(C.FPS) / 1000.0
            acc += min(frame, 0.1)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                else:
                    self.scene.handle_event(e)
            while acc >= C.DT:
                self.scene.update(C.DT)
                acc -= C.DT
            self.scene.draw(self.screen)
            pygame.display.flip()
        # leaving mid-run still counts the run
        from .scenes.arena import ArenaScene

        if isinstance(self.scene, ArenaScene) and not self.scene.finished:
            self.scene.world.dead = True
            self.scene.finish()
        self.save()
        pygame.quit()


class _NoSfx:
    enabled = False

    def play(self, name):
        pass


def simulate(frames: int) -> int:
    """Headless smoke test: autoplay a run (rendering included) for N frames."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    from . import meta
    from .scenes.arena import ArenaScene
    from .scenes.menu import MenuScene, QuestScene
    from .scenes.shop import ShopScene
    from .scenes.wheel import WheelScene

    profile = copy.deepcopy(S.DEFAULT_PROFILE)
    game = Game(headless=True, profile=profile)
    # draw every menu once
    for cls in (MenuScene, ShopScene, QuestScene, WheelScene):
        cls(game).draw(game.screen)
    for tab in range(3):
        sh = ShopScene(game)
        sh.set_tab(tab)
        sh.draw(game.screen)
    scene = ArenaScene(game, autoplay=True)
    game.goto(scene)
    deaths = 0
    best_level = 1
    for i in range(frames):
        scene.update(C.DT)
        if i % 4 == 0:
            scene.hud.evo_open = i % 400 < 200
            scene.hud.stats_open = i % 300 < 150
            scene.draw(game.screen)
        best_level = max(best_level, scene.world.player.level)
        if scene.finished:
            deaths += 1
            scene = ArenaScene(game, autoplay=True)
            game.goto(scene)
    bots = [t for t in scene.world.tanks if not t.is_player]
    evolved = sum(1 for t in bots if t.tank_name != "Basic")
    print(
        f"simulated {frames} frames: deaths={deaths} best player level={best_level} "
        f"bots={len(bots)} evolved bots={evolved} gems={profile['gems']} "
        f"rank={meta.rank(profile)}"
    )
    pygame.quit()
    return 0 if evolved > 0 else 1


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--simulate" in argv:
        i = argv.index("--simulate")
        frames = int(argv[i + 1]) if len(argv) > i + 1 else 3000
        sys.exit(simulate(frames))
    Game().run()
