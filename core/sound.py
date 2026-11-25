"""Plays the sound effects and the music.

The sound files are in assets/sounds/. They are made by tools/make_sounds.py from the
recipes in data/sounds.json, so you can change or replace any of them.

Exhibit rule: sound must never crash the game. If there is no sound card, or a file is
missing or broken, the game simply stays quiet.

How to use it from any screen:
    from core import sound
    sound.play("hit")              # a short effect, assets/sounds/hit.wav
A screen chooses its music with a class attribute, which the game loop reads every frame:
    music = "dungeon"              # plays assets/sounds/music_dungeon.wav in a loop
    music = None                   # (the default) keep whatever is playing
    music = "off"                  # silence
"""
import logging

import pygame

from core import settings
from systems.player import load_data

SOUND_DIR = settings.ROOT / "assets" / "sounds"

_config = load_data("sounds.json")
_cache = {}                                  # name -> Sound or None, so each file is read only once
_state = {"ready": False, "muted": False, "music": None}


def init():
    """Start the sound system. Call once, after pygame.init(). Returns True if sound works."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        _state["ready"] = True
    except pygame.error:
        logging.exception("No sound: the mixer could not start")
        _state["ready"] = False
    return _state["ready"]


def ready():
    return _state["ready"]


def muted():
    return _state["muted"]


def play(name):
    """Play the effect assets/sounds/<name>.wav once. Does nothing if sound is off or the file is missing."""
    if not _state["ready"] or _state["muted"]:
        return
    effect = _load(name)
    if effect is not None:
        effect.play()


def _load(name):
    if name not in _cache:
        _cache[name] = None
        path = SOUND_DIR / f"{name}.wav"
        if path.exists():
            try:
                _cache[name] = pygame.mixer.Sound(str(path))
                _cache[name].set_volume(_config["volume"]["effects"])
            except pygame.error:
                logging.exception("Could not load sound %s", path)
    return _cache[name]


def skill_sound(kind):
    """Which effect a move makes when it starts, from its look's kind (slash, projectile, rain, aura)."""
    return _config["skill_kinds"].get(kind, "swing")


def play_music(name):
    """Loop assets/sounds/music_<name>.wav. "off" stops the music. The same track is never restarted."""
    if name == _state["music"]:
        return
    _state["music"] = name
    if not _state["ready"]:
        return
    path = SOUND_DIR / f"music_{name}.wav"
    try:
        if name == "off" or not path.exists():
            pygame.mixer.music.fadeout(400)
            return
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.set_volume(0 if _state["muted"] else _config["volume"]["music"])
        pygame.mixer.music.play(loops=-1, fade_ms=600)     # loops=-1: repeat forever
    except pygame.error:
        logging.exception("Could not play music %s", path)


def current_music():
    return _state["music"]


def follow(scene):
    """Called by the game loop every frame: switch to the music the top screen asks for, if any."""
    name = getattr(scene, "music", None)
    if name:
        play_music(name)


def toggle_mute():
    """Sound on/off (the F2 key). Returns True if sound is now off."""
    _state["muted"] = not _state["muted"]
    if _state["ready"]:
        pygame.mixer.music.set_volume(0 if _state["muted"] else _config["volume"]["music"])
        if _state["muted"]:
            pygame.mixer.stop()                # cut any effect that is still playing
    return _state["muted"]


def reset():
    """Forget loaded sounds and the music choice (used by tests)."""
    _cache.clear()
    _state.update(muted=False, music=None)
