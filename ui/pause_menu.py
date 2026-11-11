"""The menu that opens when you press Esc in the dungeon (owner: B)."""
from core.strings import t
from ui.menu import MenuScene


class PauseScene(MenuScene):
    def __init__(self, game):
        options = [
            (t("pause_resume"), self.resume, True),
            (t("pause_inventory"), self.open_inventory, True),
            (t("pause_progress"), self.open_progress, True),
            (t("pause_quit"), game.go_to_title, True),
        ]
        super().__init__(game, t("pause_title"), options, under=game.scenes.current)

    def resume(self):
        self.game.scenes.pop()

    def open_inventory(self):
        from ui.inventory_screen import InventoryScene
        self.game.scenes.pop()   # close this menu first, so the bag opens on top of the dungeon
        self.game.scenes.push(InventoryScene(self.game))

    def open_progress(self):
        from ui.stats_screen import StatsScene
        self.game.scenes.pop()
        self.game.scenes.push(StatsScene(self.game))

    def on_escape(self):
        self.resume()
