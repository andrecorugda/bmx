# not-burxt: neutral — takes an arbitrary implementation command — in Burxt, nobody without the toolchain could run it
"""What a document must not be able to make the output do — the part of `ESCAPING.md` nothing tested.

    python3 tests/output.py "node reference/bmx.js --render" ./bmxrender

**`ESCAPING.md` said "the conformance suite tests this" and pointed at `tests/pass/bmx_library.bx` in
the Burxt repository — a path that went away with the `lib/` migration.** So the security-critical half
of the escaping contract was asserted by a sentence rather than by a test, and the sentence named a file
that no longer exists.

`tests/renders.py` was the nearest thing, and it is not enough: it compares the two renderers and treats
*both refusing* as agreement. If both stopped refusing `javascript:`, it would still pass. **Agreement is
a check on drift, never on correctness** — the same lesson the `#one,#two` hole taught, arriving in the
one place where being wrong is an attack rather than a typo.

So this asserts the OUTCOME, per renderer: a target renders or refuses, and a document cannot put an
attribute into the output through a code fence's info string. It also pins the case folding, because a
URI scheme is case-insensitive (RFC 3986 §3.1) and `HTTPS://example.com` was refused until 0.11 — a false
refusal of correct input, which is the class a conformance suite cannot hold.

**The info-string half was found by grepping this project's own prose for verbs**, not by reading code.
`docs/styling.md` says *"the info string is checked as a name before it becomes a class, so a document
cannot inject an attribute through it"* — which is TRUE, and was asserted by nothing. Every fixture used
`burxt` or `js`. star-burxt named the family: **a claim in prose is a specification nobody runs**, and
the grep is for the verbs — *checked*, *refused*, *cannot*, *tested* — then asking of each whether
anything would notice if it stopped being true.
"""

import pathlib
import shlex
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from probe import speaks  # noqa: E402

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


# A code fence's info string becomes `class="language-<info>"`, so it is the one place a DOCUMENT's own
# bytes reach an attribute. Anything that is not a name must produce no class at all — not an escaped
# one, not a truncated one. (target, must the output contain a class?)
INFO_STRINGS = [
    ("burxt", True),
    ("js", True),
    ("c-sharp", True),                     # the name rule allows `-`
    ('x" onload="steal()', False),         # the attack this claim is about
    ("a b", False),                        # a space is not a name
    ("a<b>", False),
    ("../etc", False),
    ("1abc", False),                       # a name starts with a letter
]


def check_info(renderer):
    """Assert the class appears only for a valid name, and that nothing else leaks into the tag."""
    failures = 0
    for info, wants_class in INFO_STRINGS:
        open("/tmp/bmx-info.bmx", "w").write(f"```{info}\ncode\n```\n")
        r = subprocess.run(shlex.split(renderer) + ["/tmp/bmx-info.bmx"], capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip()
        has_class = 'class="language-' in out
        # The bytes must not appear inside the opening tag at all — an escaped attribute is still a
        # document deciding the shape of the tag.
        tag = out.split("<code", 1)[-1].split(">", 1)[0] if "<code" in out else ""
        leaked = any(ch in tag for ch in ('"', "<", ">", " onload")) and not wants_class
        if has_class != wants_class or leaked:
            failures += 1
            print(f"    FAIL  info {info!r}: class={has_class} want={wants_class} tag={tag[:40]!r}")
    print(f"    {len(INFO_STRINGS)} info strings checked")
    return failures


def main():
    renderers = sys.argv[1:]
    if not renderers:
        print("usage: output.py <renderer> [<renderer> …]")
        return 1

    for renderer in renderers:
        speaks(renderer, "page")

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
        failures += check_info(renderer)

    print()
    if failures:
        print(f"{failures} failed")
        return 1
    print("no document can reach the output through a target or an info string")
    return 0


if __name__ == "__main__":
    sys.exit(main())
