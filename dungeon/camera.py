"""The camera decides which part of a big floor is shown on screen. No pygame here.

"World" positions are pixels on the whole floor. "Screen" positions are pixels inside
the part of the window where the dungeon is drawn (the view).
The camera stores the world position of the view's top-left corner in self.x, self.y.
"""

FOLLOW_SPEED = 10   # higher = the camera catches up with the player faster


def _clamp_axis(wanted, view_size, world_size):
    """Keep the view inside the world on one axis (x or y)."""
    if world_size <= view_size:
        # The floor is smaller than the view: centre it (the result is zero or negative).
        return (world_size - view_size) / 2
    return max(0, min(wanted, world_size - view_size))


class Camera:
    def __init__(self, view_w, view_h, world_w, world_h):
        self.view_w, self.view_h = view_w, view_h
        self.world_w, self.world_h = world_w, world_h
        self.x = 0.0
        self.y = 0.0

    def _target(self, center_x, center_y):
        """Where the camera wants to be so that (center_x, center_y) is in the middle of the view."""
        return (_clamp_axis(center_x - self.view_w / 2, self.view_w, self.world_w),
                _clamp_axis(center_y - self.view_h / 2, self.view_h, self.world_h))

    def snap_to(self, center_x, center_y):
        """Jump straight to the target (used when a floor starts)."""
        self.x, self.y = self._target(center_x, center_y)

    def move_towards(self, center_x, center_y, dt):
        """Glide a part of the way to the target each frame, so the view moves smoothly."""
        target_x, target_y = self._target(center_x, center_y)
        step = min(1.0, FOLLOW_SPEED * dt)   # never overshoot, even on a very slow frame
        self.x += (target_x - self.x) * step
        self.y += (target_y - self.y) * step

    def to_screen(self, world_x, world_y):
        """Turn a world position into a position inside the view."""
        return round(world_x - self.x), round(world_y - self.y)
