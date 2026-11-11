# Running Stungeon at the exhibit

Two ways to put the game on the exhibit laptop. Both work with no internet.

## Way 1: the built folder (no Python needed on the laptop)

On a team computer, in the repo folder with the virtual environment active:

```
pip install -r requirements-build.txt
python tools/build.py
```

This makes `dist/Stungeon/` (about 33 MB). Copy that whole folder to the laptop and to the USB stick.

On the laptop:

- `Stungeon.exe --fullscreen` starts the game.
- `Stungeon.exe --fullscreen --demo` skips the title menu and starts the demo run at once.
- The easiest way to pass these options: right-click `Stungeon.exe`, choose **Create shortcut**,
  open the shortcut's **Properties**, and add ` --fullscreen` at the end of **Target**.

The built game writes two things next to `Stungeon.exe`:

- `logs/error.log`: if something goes wrong, the game goes back to the title menu and the error is written here.
- `saves/save.json`: the saved game. Delete it to remove "Continue" from the title menu.

Build again after every code or data change: the folder does not update itself.

## Way 2: from the repo (Python needed)

Follow the setup steps in the README on the laptop, then double-click `run_game.bat`.
It starts the game fullscreen. `run_game.bat --demo` starts the demo at once.

## Demo mode

- On the title menu, **F1** (or the Demo button) starts the demo.
- The demo's class and seed are in `data/demo.json`, so every demo run has the same floors.
- The demo has fewer enemies and is never saved.

## Before the exhibit, check on the real laptop

- [ ] The game fills the screen and the text is readable.
- [ ] A full demo run from start to end screen, with the laptop's own keyboard and mouse.
- [ ] `logs/error.log` is empty after that run.
- [ ] The laptop does not go to sleep or show notifications during a run.
