# How the screenshots in the docs are made

**Every rendered panel on the documentation site is real output from a real renderer.** None is a
mock-up and none is hand-written HTML, because a picture of what the format *ought* to produce is
the same defect as a spec sentence nobody ran.

    burxt build render.bx -o bmxrender      # the level-1 renderer, from burxt/bmx.bx
    burxt build page.bx -o page && ./page ex2        # source + rendered, side by side
    burxt build errpage.bx -o errpage && ./errpage err1   # source + the refusal
    burxt build fmt.bx -o fmt && ./fmt ../docs/*.md   # indent every example, one per open block
    burxt build migrate-0.7.bx -o migrate-0.7 && ./migrate-0.7 FILE...   # 0.6 fences -> 0.7, tracking a stack
    burxt build showcase.bx -o showcase && ./showcase   # the landing page, LIVE HTML -> docs/_includes/
    node shot.mjs ex1 ex2 ex3 err1 editor skins        # -> PNG, 2x, cropped to the panels

`shot.mjs` uses the puppeteer that is already on this machine rather than installing a second
browser. If the path in it goes stale, that is the one line to fix.

## The landing page is not a screenshot

`showcase.bx` generates `docs/_includes/showcase.html` — **live HTML**, and the only rendered thing on
the site that is not a picture. It is the one place a **split** has to be visible: the navigation,
search and buttons are the SITE's furniture drawn in CSS, and only the page region is what the document
produced. BMX has no syntax for a nav bar and none for an image (`SPEC.md` §7), so the generous reading
has to be closed off — and a caption doing it is weak, because the first impression already landed.

So the showcase is a **slider over three slides** — the bar, the content, the whole page — and the half
you are not looking at goes soft. Andre's design, and better than a caption, because the whole page stays
on screen and you see WHERE the split falls instead of reading about it.

## What is NOT the boundary, measured

Two versions of this showcase put a `layout.html` beside the document, on the theory that BMX cannot
express a navigation bar. Andre asked *"you really need html?"*, and `bmxrender` answered:

    # Roast&Co            ->   <h1>Roast&amp;Co</h1>
    - [Coffee](/coffee)   ->   <ul><li><a href="/coffee">Coffee</a></li> ...

A bar is a brand and a row of links, and both render today — the whole shop page, search pill and buttons
included, comes out of `shop.bmx` and a stylesheet. **The real limit is one step narrower: BMX has no
ATTRIBUTE syntax.** So the stylesheet reaches the bar by position (`.bmx > h1` is the brand, the first
`p` is the links) rather than by class, and a positional selector is brittle — insert a paragraph and the
bar restyles. `:nav:` is the mechanism that fixes it: a block names the region, a host that declares
`nav` renders it however it likes, and `bmxrender` refuses blocks by design (`BMX-R003`) because deciding
what `nav` means is not the format's job. The landing page says all of this rather than hiding it.

This is worth remembering as a shape, not just a fact: **the wall was a caption I had written, not a
property of the format.** It cost nothing to check — one file and one render.

`editor.bmx` is the one on [In your editor](https://bmx.burxt-lang.org/editor.html), and it shows the
same level-1 output the preview shows — so it is a real picture of the preview rather than a staged
one, and it goes stale the moment the renderer does.

**Regenerate whenever the renderer's output changes.** A screenshot is the one artefact on the
site that cannot fail a test when it goes stale — `docs/` has no check that an image still matches
what the code does, which is exactly why the pipeline lives here in the repository rather than in
somebody's shell history.

## `fmt.bx` is a gate, not a convenience

CI runs `fmt --check` over every page, because **indentation is insignificant to the parser and
therefore invisible to every other check.** An example indented wrongly parses perfectly and teaches a
reader the wrong shape, which is worse than a broken example — a broken one gets fixed.

It also found the defect that produced 0.8. Round-tripping the conformance suite through it — indent,
reparse, compare — made two fixtures stop parsing, because `BMX-E012` was refusing an indented list
inside a block. Nothing in the suite could have caught that: every case was written by someone who
believed the rule. **The tool that consumes a rule is what finds the rule too broad.**
