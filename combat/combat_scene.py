"""The fight (owner: B).

PLACEHOLDER: shows nothing and ends the fight as a win on any key press.
B builds the real turn-based combat here. Keep the __init__ signature and the result dict.
"""
import pygame

from core.scene import Scene


class CombatScene(Scene):
    def __init__(self, game, player, enemy, on_end):
        super().__init__(game)
        self.player = player
        self.enemy = enemy
        self.on_end = on_end   # called once with the result dict below

    def finish(self, won, fled=False):
        result = {"won": won, "fled": fled, "xp": 0, "gold": 0, "loot": []}
        self.game.scenes.pop()
        self.on_end(result)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.finish(won=True)
