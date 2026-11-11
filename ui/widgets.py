"""Small drawing helpers shared by all screens (owner: B)."""
import pygame

from ui import theme

# Characters the default font cannot draw (they would show as boxes) -> what to draw instead.
# The question bank uses "→" in 162 plural questions.
_REPLACEMENTS = {"→": "->"}


def drawable(string):
    for char, plain in _REPLACEMENTS.items():
        string = string.replace(char, plain)
    return string


def text(surface, font, string, color, pos, anchor="topleft"):
    """Draw one line of text. anchor says which point of the text sits at pos. Returns its rect."""
    image = font.render(drawable(string), True, color)
    rect = image.get_rect(**{anchor: pos})
    surface.blit(image, rect)
    return rect


def wrap(font, string, width):
    """Split a string into lines that fit inside `width` pixels."""
    lines, line = [], ""
    for word in drawable(string).split():
        test = f"{line} {word}".strip()
        if font.size(test)[0] <= width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def wrapped(surface, font, string, color, topleft, width, line_gap=6):
    """Draw text over several lines. Returns the y just below the last line."""
    x, y = topleft
    for line in wrap(font, string, width):
        text(surface, font, line, color, (x, y))
        y += font.get_height() + line_gap
    return y


_dim_cover = None   # made once, the first time dim() is used


def dim(surface):
    """Darken everything drawn so far, so a menu on top of the game is easy to read."""
    global _dim_cover
    if _dim_cover is None or _dim_cover.get_size() != surface.get_size():
        _dim_cover = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        _dim_cover.fill((0, 0, 0, 170))
    surface.blit(_dim_cover, (0, 0))


def bar(surface, rect, value, maximum, color, back, label="", font=None):
    """A bar that shows value out of maximum (HP, resource), with an optional label on it."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, theme.OUTLINE, rect)
    inside = rect.inflate(-4, -4)
    pygame.draw.rect(surface, back, inside)
    if maximum > 0 and value > 0:
        filled = inside.copy()
        filled.width = max(1, round(inside.width * min(value, maximum) / maximum))
        pygame.draw.rect(surface, color, filled)
        # A lighter line along the top makes the bar look slightly rounded.
        lighter = tuple(min(255, c + 40) for c in color)
        pygame.draw.line(surface, lighter, filled.topleft, (filled.right - 1, filled.top))
    if label and font:
        text(surface, font, label, theme.TEXT, rect.center, "center")
