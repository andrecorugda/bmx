# How the screenshots in the docs are made

**Every rendered panel on the documentation site is real output from a real renderer.** None is a
mock-up and none is hand-written HTML, because a picture of what the format *ought* to produce is
the same defect as a spec sentence nobody ran.

    burxt build render.bx -o bmxrender      # the level-1 renderer, from burxt/bmx.bx
    python3 page.py ex2                     # source + rendered, side by side
    python3 errpage.py err1                 # source + the refusal
    node shot.mjs ex1 ex2 ex3 err1 editor skins   # -> PNG, 2x, cropped to the panels

`shot.mjs` uses the puppeteer that is already on this machine rather than installing a second
browser. If the path in it goes stale, that is the one line to fix.

`editor.bmx` is the one on [In your editor](https://bmx.burxt-lang.org/editor.html), and it shows the
same level-1 output the preview shows — so it is a real picture of the preview rather than a staged
one, and it goes stale the moment the renderer does.

**Regenerate whenever the renderer's output changes.** A screenshot is the one artefact on the
site that cannot fail a test when it goes stale — `docs/` has no check that an image still matches
what the code does, which is exactly why the pipeline lives here in the repository rather than in
somebody's shell history.
