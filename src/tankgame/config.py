"""Screen, arena and color constants."""

SCREEN_W, SCREEN_H = 1280, 800
FPS = 60
DT = 1.0 / FPS

ARENA_SIZE = 6000  # world is ARENA_SIZE x ARENA_SIZE, origin top-left
NEST_RADIUS = 900  # pentagon nest in the middle of the map
GRID_CELL = 128  # spatial hash cell size
BOT_COUNT = 12
SPAWN_IMMUNITY = 5.0  # seconds, like the original

# Diep-style palette
BG = (205, 205, 205)
BG_GRID = (195, 195, 195)
BG_OUTSIDE = (183, 183, 183)
BG_NEST = (192, 189, 200)
BARREL = (153, 153, 153)
PLAYER_COLOR = (0, 178, 225)
ENEMY_COLOR = (241, 78, 84)
SQUARE_COLOR = (255, 232, 105)
TRIANGLE_COLOR = (252, 118, 119)
PENTAGON_COLOR = (118, 141, 252)
SHINY_COLOR = (140, 255, 110)
FREEZE_COLOR = (150, 220, 255)
FLAME_COLOR = (255, 150, 40)
LASER_COLOR = (255, 90, 220)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TEXT = (240, 240, 240)
UI_PANEL = (60, 60, 70)
UI_ACCENT = (0, 178, 225)
GEM_COLOR = (90, 220, 255)
HP_GREEN = (133, 227, 125)
XP_YELLOW = (255, 222, 67)


def darken(color, f=0.75):
    return tuple(max(0, int(c * f)) for c in color[:3])
