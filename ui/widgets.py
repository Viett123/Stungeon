"""Small drawing helpers shared by all screens (owner: B)."""
import pygame

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


def bar(surface, rect, value, maximum, color, back=(50, 44, 60)):
    """A filled bar, e.g. HP. rect = (x, y, w, h)."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, back, rect, border_radius=4)
    if maximum > 0 and value > 0:
        filled = rect.copy()
        filled.width = max(1, round(rect.width * min(value, maximum) / maximum))
        pygame.draw.rect(surface, color, filled, border_radius=4)


def panel(surface, rect, color=(30, 25, 40), border=(80, 70, 100)):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, width=2, border_radius=8)
    return rect
