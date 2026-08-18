"""What a renderer must do with a link target — the third thing `ESCAPING.md` requires, now tested.

    python3 tests/targets.py "node reference/bmx.js" ./bmxrender

**`ESCAPING.md` said "the conformance suite tests this" and pointed at `tests/pass/bmx_library.bx` in
the Burxt repository — a path that went away with the `lib/` migration.** So the security-critical half
of the escaping contract was asserted by a sentence rather than by a test, and the sentence named a file
that no longer exists.

`tests/renders.py` was the nearest thing, and it is not enough: it compares the two renderers and treats
*both refusing* as agreement. If both stopped refusing `javascript:`, it would still pass. **Agreement is
a check on drift, never on correctness** — the same lesson the `#one,#two` hole taught, arriving in the
one place where being wrong is an attack rather than a typo.

So this asserts the OUTCOME, per renderer, for each target: rendered, or refused. It also pins the case
folding, because a URI scheme is case-insensitive (RFC 3986 §3.1) and `HTTPS://example.com` was refused
until 0.11 — a false refusal of correct input, which is the class a conformance suite cannot hold.
"""

import shlex
import subprocess
import sys

# (target, must render?) — the reason each one is here matters more than the list.
TARGETS = [
    ("https://a.example", True),        # the ordinary case
    ("http://a.example", True),
    ("mailto:a@b.c", True),
    ("/relative/path", True),           # no scheme at all
    ("../up", True),
    ("/has:colon/after/slash", True),   # a colon that is not a scheme, because a slash precedes it
    # **Case folding.** RFC 3986 §3.1: schemes are case-insensitive. Refusing these refused correct URLs.
    ("HTTPS://a.example", True),
    ("Https://a.example", True),
    ("MAILTO:a@b.c", True),
    # **And folding cannot open a hole, because the list is an ALLOW-list.** Every casing still refuses.
    ("javascript:steal()", False),
    ("JAVASCRIPT:steal()", False),
    ("JaVaScRiPt:steal()", False),
    ("data:text/html;base64,x", False),
    ("vbscript:x", False),
    ("file:///etc/passwd", False),
    ("a:b", False),                     # an unknown scheme is refused, not stripped
]


def main():
    renderers = sys.argv[1:]
    if not renderers:
        print("usage: targets.py <renderer> [<renderer> …]")
        return 1

    failures = 0
    for renderer in renderers:
        print(f"  {renderer}")
        for target, must_render in TARGETS:
            doc = f"[x]({target})\n"
            open("/tmp/bmx-target.bmx", "w").write(doc)
            r = subprocess.run(shlex.split(renderer) + ["/tmp/bmx-target.bmx"],
                               capture_output=True, text=True)
            out = (r.stdout + r.stderr).strip()
            refused = "BMX-R001" in out
            rendered = target in out and not refused
            good = rendered if must_render else refused
            if not good:
                failures += 1
                want = "render" if must_render else "refuse"
                print(f"    FAIL  {target!r} must {want}, got: {out[:70]}")
        print(f"    {len(TARGETS)} targets checked")

    print()
    if failures:
        print(f"{failures} failed")
        return 1
    print("every target renders or refuses as the escaping contract requires")
    return 0


if __name__ == "__main__":
    sys.exit(main())
