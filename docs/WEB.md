# Playing Stungeon in a web browser

The game can run in a browser, so people can test it without installing Python.
We use **pygbag**: it turns the Python game into a web page that runs Python as WebAssembly.

## Build it

```
pip install pygbag            # once, in the .venv
python tools/build_web.py     # makes build/stungeon_web.zip
```

You also need `ffmpeg` on the PATH, because browsers can't play every WAV file, so the
script turns the sounds into OGG.

To try it on your own computer first:

```
python tools/build_web.py --serve
```

Then open http://localhost:8000 and click once on the page. Browsers only allow sound
after a click, so pygbag waits for one.

Use `--serve` for testing, not a plain `python -m http.server`. On localhost the page asks
for pygame at `localhost:8000/cdn/...`, and only pygbag's own test server can answer that.
On a real website it gets pygame from pygbag's public CDN instead.

## Put it on itch.io

1. Make an account on https://itch.io, then **Dashboard → Create new project**.
2. Kind of project: **HTML**.
3. Upload `build/stungeon_web.zip` and tick **"This file will be played in the browser"**.
4. Viewport: **1280 × 720**. Tick **"Fullscreen button"**.
5. Visibility: **Restricted** with a password, if only testers should see it. Use **Public**
   when everyone may play.
6. Save, then open the page and click once to start.

## Things to know

- **The first load is slow**, about 10 to 20 seconds, because the browser downloads Python and
  pygame first (about 10 MB). After that the browser keeps them in its cache.
- **Saves** live in the browser's storage for that site. Clearing site data, using a private
  window or switching to another browser starts fresh. (We have not tested yet whether a save
  survives closing the tab.)
- **The code is not secret.** The game ships as `stungeon.apk`, which is really a zip of our
  Python files and the question banks. Anyone who downloads it can unzip and read them. This is
  the same as the public GitHub repo. A web build cannot hide Python code; a licence (who may
  reuse it) is what protects it.
- **Two rules for the code**, or the web build breaks:
  - `main.py` must keep `import pygame` at the top. pygbag reads main.py's imports to know
    that it must download pygame.
  - Never block the game loop (already a project rule). In the browser, `Game.run_async()`
    gives control back to the page after every frame. A `time.sleep` or `input()` would freeze
    the tab.
