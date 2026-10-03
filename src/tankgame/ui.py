"""Small UI toolkit: fonts, outlined text, panels and buttons."""

import pygame

from . import config as C

_fonts: dict[int, pygame.font.Font] = {}


def font(size: int) -> pygame.font.Font:
    f = _fonts.get(size)
    if f is None:
        f = pygame.font.Font(None, size)
        f.set_bold(True)
        _fonts[size] = f
    return f


def text(surf, s, size, pos, color=C.TEXT, anchor="topleft", outline=True):  # noqa: PLR0913, PLR0917
    f = font(size)
    img = f.render(str(s), True, color)
    rect = img.get_rect(**{anchor: pos})
    if outline:
        shadow = f.render(str(s), True, (40, 40, 40))
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            surf.blit(shadow, rect.move(dx, dy))
    surf.blit(img, rect)
    return rect


def panel(surf, rect, color=C.UI_PANEL, alpha=225, radius=10):
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius)
    surf.blit(s, rect.topleft)


def bar(surf, rect, frac, color, back=(40, 40, 40), radius=8):
    pygame.draw.rect(surf, back, rect, border_radius=radius)
    if frac > 0:
        inner = rect.inflate(-4, -4)
        inner.width = max(2, int(inner.width * min(1.0, frac)))
        pygame.draw.rect(surf, color, inner, border_radius=radius)


class Button:
    def __init__(self, rect, label, action=None, color=C.UI_ACCENT, size=30, enabled=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.color = color
        self.size = size
        self.enabled = enabled

    def draw(self, surf):
        hover = self.rect.collidepoint(pygame.mouse.get_pos()) and self.enabled
        col = self.color if self.enabled else (110, 110, 110)
        if hover:
            col = tuple(min(255, c + 30) for c in col)
        pygame.draw.rect(surf, C.darken(col, 0.6), self.rect.move(0, 4), border_radius=10)
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        text(surf, self.label, self.size, self.rect.center, anchor="center")

    def handle(self, event) -> bool:
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.enabled
            and self.rect.collidepoint(event.pos)
        ):
            if self.action:
                self.action()
            return True
        return False


def gem_icon(surf, center, size=10):
    x, y = center
    pts = [
        (x, y - size),
        (x + size * 0.8, y - size * 0.3),
        (x, y + size),
        (x - size * 0.8, y - size * 0.3),
    ]
    pygame.draw.polygon(surf, C.GEM_COLOR, pts)
    pygame.draw.polygon(surf, C.darken(C.GEM_COLOR, 0.6), pts, 2)


def gems_label(surf, amount, pos, size=32, anchor="topleft"):
    r = text(
        surf,
        f"{int(amount):,}",
        size,
        (pos[0] + 26, pos[1]) if anchor == "topleft" else pos,
        color=C.GEM_COLOR,
        anchor=anchor,
    )
    gem_icon(surf, (r.left - 15, r.centery), size // 3)
    return r
