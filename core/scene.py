"""Scenes are the screens of the game (title, dungeon, combat, shop...).

Every scene has the same three methods, and the Game calls them once per frame:
    handle_event(event)  ->  react to a key press or mouse click
    update(dt)           ->  move things; dt = seconds since the last frame
    draw(surface)        ->  paint the scene onto the screen
"""


class Scene:
    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


class SceneManager:
    """A stack of scenes. The top one is active.

    push    -> open a scene on top (e.g. combat over the dungeon); pop goes back to the one below.
    replace -> swap the whole stack for one scene (e.g. back to the title screen).
    """

    def __init__(self):
        self._stack = []

    @property
    def current(self):
        return self._stack[-1] if self._stack else None

    def push(self, scene):
        self._stack.append(scene)

    def pop(self):
        if self._stack:
            self._stack.pop()

    def replace(self, scene):
        self._stack = [scene]
