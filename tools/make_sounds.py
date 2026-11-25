"""Make every sound and music file of the game from data/sounds.json (a build helper, not part of the game).

We make our own sounds in code, so there is nothing to license or credit. They are simple
"chiptune" sounds, like old game consoles made: a few basic waves, mixed together.

How a sound is made (first-year version):
- A sound file is a long list of numbers between -1 and 1 ("samples"), 22,050 of them per second.
  The speaker moves in and out following those numbers.
- A wave repeats itself `freq` times per second. More repeats per second = a higher note.
- An "envelope" makes the sound fade in (attack) and fade out, so it does not click.
- Several "layers" (or music tracks) are added together, then saved as a .wav file.

Change a number in data/sounds.json and run this again to get new sounds:
    python tools/make_sounds.py
It writes assets/sounds/<name>.wav for every effect and assets/sounds/music_<name>.wav for every track.
Only the Python standard library is used, so nothing has to be installed.
"""
import json
import math
import random
import struct
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / "data" / "sounds.json"
OUT_DIR = ROOT / "assets" / "sounds"

NOTE_STEPS = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}   # half steps from A
RELEASE_SECONDS = 0.02      # every note fades out over its last 20 ms, so notes never click
DRUMS = {
    # How each drum letter in a music track sounds. Same fields as an effect layer.
    "k": {"wave": "sine", "freq": 140, "to": 45, "seconds": 0.18, "volume": 1.0},                  # kick
    "s": {"wave": "noise", "freq": 9000, "seconds": 0.14, "volume": 0.7},                         # snare
    "h": {"wave": "noise", "freq": 22050, "seconds": 0.04, "volume": 0.35},                       # hi-hat
}


def note_hz(name):
    """Turn a note name like "A4", "C#5" or "Bb3" into its frequency in Hz (A4 = 440 Hz)."""
    letter, rest = name[0].upper(), name[1:]
    step = NOTE_STEPS[letter]
    while rest and rest[0] in "#b":
        step += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    octave = int(rest)
    # Every octave doubles the frequency; one half step multiplies it by the 12th root of 2.
    return 440.0 * 2 ** ((step + 12 * (octave - 4)) / 12)


def wave_value(kind, phase, duty=0.5):
    """The height of one wave at `phase` (0.0 to 1.0 through one repeat), between -1 and 1."""
    if kind == "square":
        return 1.0 if phase < duty else -1.0
    if kind == "triangle":
        return 4 * phase - 1 if phase < 0.5 else 3 - 4 * phase
    if kind == "saw":
        return 2 * phase - 1
    if kind == "sine":
        return math.sin(2 * math.pi * phase)
    raise ValueError(f"unknown wave {kind!r}")


def tone(layer, rate, rng):
    """Make one layer: a wave sliding from `freq` to `to`, shaped by its envelope. Returns samples."""
    seconds = layer["seconds"]
    count = int(seconds * rate)
    start, end = layer["freq"], layer.get("to", layer["freq"])
    attack = layer.get("attack", 0.005)
    volume = layer.get("volume", 1.0)
    duty = layer.get("duty", 0.5)
    vibrato = layer.get("vibrato", 0)       # how many times per second the pitch wobbles
    samples = []
    phase = 0.0
    noise = 0.0
    for i in range(count):
        t = i / rate
        done = i / count                    # 0.0 at the start, 1.0 at the end
        freq = start + (end - start) * done  # the slide: a straight line from start to end
        if vibrato:
            freq *= 1 + 0.03 * math.sin(2 * math.pi * vibrato * t)
        old = phase
        phase = (phase + freq / rate) % 1.0
        if layer["wave"] == "noise":
            # Noise: a new random height `freq` times per second. Low freq = rumble, high = hiss.
            if phase < old or i == 0:
                noise = rng.uniform(-1, 1)
            value = noise
        else:
            value = wave_value(layer["wave"], phase, duty)
        envelope = min(1.0, t / attack) if attack else 1.0
        envelope *= (1 - done) ** layer.get("fade", 1.0)   # fade: 1 = straight down, 2 = quick drop
        samples.append(value * envelope * volume)
    return samples


def mix_into(target, samples, at):
    """Add `samples` into `target`, starting at position `at`. `target` grows if needed."""
    need = at + len(samples)
    if len(target) < need:
        target.extend([0.0] * (need - len(target)))
    for i, value in enumerate(samples):
        target[at + i] += value


def make_effect(recipe, rate, rng):
    """One sound effect: its layers mixed together. A layer with "notes" plays them one after another."""
    out = []
    for layer in recipe["layers"]:
        at = int(layer.get("delay", 0) * rate)
        if "notes" in layer:
            for note in layer["notes"]:
                mix_into(out, tone(dict(layer, freq=note_hz(note), to=note_hz(note)), rate, rng), at)
                at += int(layer["step"] * rate)
        else:
            mix_into(out, tone(layer, rate, rng), at)
    return finish(out, recipe.get("volume", 1.0))


def steps_of(track):
    """The steps of a music track as a list. The "|" bar lines are only there to help people read it."""
    return [token for token in track["steps"].split() if token != "|"]


def make_music(song, rate, rng):
    """One music loop. Each track is a row of steps; a step is one eighth of a bar when steps_per_beat is 2.

    In a melody track:  a note name starts a note, "-" holds the note longer, "." is silence.
    In a drum track:    k = kick, s = snare, h = hi-hat, "." = silence.
    """
    step_seconds = 60 / song["bpm"] / song.get("steps_per_beat", 2)
    tracks = [(track, steps_of(track)) for track in song["tracks"]]
    length = max(len(steps) for _, steps in tracks)
    out = [0.0] * int(length * step_seconds * rate)
    for track, steps in tracks:
        for i, token in enumerate(steps):
            at = int(i * step_seconds * rate)
            if track["wave"] == "drums":
                for letter in token if token != "." else "":
                    drum = dict(DRUMS[letter], volume=DRUMS[letter]["volume"] * track.get("volume", 1.0))
                    mix_into(out, tone(drum, rate, rng), at)
            elif token not in ("-", "."):
                held = 1
                while i + held < len(steps) and steps[i + held] == "-":
                    held += 1
                layer = dict(track, freq=note_hz(token), seconds=held * step_seconds)
                layer["to"] = layer["freq"]
                samples = tone(layer, rate, rng)
                fade = int(RELEASE_SECONDS * rate)
                for j in range(max(0, len(samples) - fade), len(samples)):
                    samples[j] *= (len(samples) - j) / fade
                mix_into(out, samples, at)
    # The loop must be exactly the length of its steps, so it repeats on the beat.
    return finish(out[: int(length * step_seconds * rate)], song.get("volume", 1.0))


def finish(samples, volume):
    """Scale the loudest point to `volume` (so every file is about as loud as planned) and clip to -1..1."""
    peak = max((abs(v) for v in samples), default=0.0) or 1.0
    return [max(-1.0, min(1.0, v / peak * volume)) for v in samples]


def write_wav(path, samples, rate):
    """Save samples as a 16-bit mono .wav file."""
    data = b"".join(struct.pack("<h", round(v * 32767)) for v in samples)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(data)


def build(recipes, out_dir):
    """Make every file. The random noise uses a fixed seed, so the same recipe always gives the same file."""
    rate = recipes["sample_rate"]
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, recipe in recipes["effects"].items():
        write_wav(out_dir / f"{name}.wav", make_effect(recipe, rate, random.Random(name)), rate)
        written.append(name)
    for name, song in recipes["music"].items():
        write_wav(out_dir / f"music_{name}.wav", make_music(song, rate, random.Random(name)), rate)
        written.append(f"music_{name}")
    return written


if __name__ == "__main__":
    only = sys.argv[1:]          # optional: python tools/make_sounds.py hit correct  (just those)
    recipes = json.loads(RECIPES.read_text(encoding="utf-8"))
    if only:
        recipes["effects"] = {k: v for k, v in recipes["effects"].items() if k in only}
        recipes["music"] = {k: v for k, v in recipes["music"].items() if k in only}
    for name in build(recipes, OUT_DIR):
        print("wrote", name)
