#!/usr/bin/env python3
# not-burxt: gap — checks THIS REPOSITORY rather than the format, so the standalone argument never reached it
"""The invitation on the site is a command that works.

    python3 tests/invitation.py
    python3 tests/invitation.py --prove-it     # the negative control

**`README.md` promised "any language can implement BMX" and `docs/` did not mention `tests/harness.py`
once.** Grepped by the star-burxt session across every page: zero hits, and nothing under `docs/`
matched *implement BMX*, *your own implementation* or *another language* either. So the capability was
real — the harness takes an arbitrary command string, and a stranger can conform in an afternoon — and
the invitation existed only in the repository, which a reader of the documentation site never opens.

Worse than absent: **mis-routed.** `install.md`'s "In any other language" sent that reader to
[Building on BMX], whose first sentence says it is for layers *above* the format. The one contributor
this project needs most — 1.0 requires an implementation by somebody who did not write the spec — met
the page that was not for them and stopped.

That is the same family as the defect star-burxt had just fixed on their own install page, and the
same family as `tests/output.py`: **a claim in prose is a specification nobody runs.** A page carrying
a command is a claim. So this runs it.

What it asserts, and why each one is a thing that would actually break:

1. the implementer page exists and names the runner a stranger is told to use;
2. every runner the page names is a file that is there — a rename elsewhere silently guts the page;
3. the harness's output still has the shape the page prints, since the page teaches a reader what
   success and failure look like before they have ever run it;
4. the suite is at least as large as the two pages claim in prose.

**It does not pin the pass count**, and that is deliberate: a gate that fires when somebody adds a
conformance case is a gate that argues against the thing this project wants to be frictionless.
"""

import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PAGE = ROOT / "docs" / "implementing.md"

# The prose floor: the suite's size, stated in words on the pages that describe it rather than as a
# number anybody maintains. **Discovered, not listed** — `tests/version.py` held a literal list of six
# pages and a new page escaped its gate in silence, which is how `docs/index.md` came to claim 0.4 for
# eight minors. A check whose scope is hand-written has the same blind spot as the claim it guards.
FLOOR = 90
CLAIM = "more than ninety"

failures = []


def check(name, condition, detail=""):
    if condition:
        print("  ok    %s" % name)
    else:
        print("  FAIL  %s%s" % (name, ("\n          " + detail) if detail else ""))
        failures.append(name)


def main():
    broken = "--prove-it" in sys.argv

    check("the implementer page is on the site", PAGE.is_file(), "%s is missing" % PAGE)
    if not PAGE.is_file():
        sys.exit(1)
    page = PAGE.read_text()

    # 1 + 2. The page names runners; a runner named on a page and absent from the tree is the
    # failure this file is named after, one level down.
    named = sorted(set(re.findall(r"tests/([a-z_]+\.py)", page)))
    check("the page tells a stranger which runner to use", "harness.py" in named,
          "the page names %r" % named)
    missing = [n for n in named if not (HERE / n).is_file()]
    check("every runner the page names exists", not missing, "named but absent: %s" % missing)

    # 3. The shape the page prints, from the runner rather than from memory. The control hands it a
    # command that is not a BMX parser — the wrong-binary case `probe.py` exists for — so the shape
    # check has nothing to match and must say so.
    command = "node reference/bmx.js" if not broken else "node reference/bmx.js --render"
    run = subprocess.run(
        [sys.executable, str(HERE / "harness.py"), command],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    last = [l for l in run.stdout.strip().splitlines() if l.strip()]
    tally = re.match(r"^(\d+) cases, (\d+) passed, (\d+) failed$", last[-1]) if last else None
    check("the harness still prints the count the page shows", tally is not None,
          "last line was %r" % (last[-1] if last else ""))

    if tally:
        total, passed, failed = (int(g) for g in tally.groups())
        check("the count is self-consistent, as the page's example is",
              passed + failed == total, "%d + %d != %d" % (passed, failed, total))

        # 4. The prose floor, on every page that states it. A shrinking suite would make all of them
        # wrong at once and none of them would say so.
        #
        # **This check is also what stops a green run over an evaporated suite**, which is the half the
        # star-burxt session asked about: this file deliberately refuses to pin the pass count, and a
        # harness that has stopped finding cases at all reports `0 cases, 0 passed, 0 failed` — a shape
        # that matches, and a tally that is self-consistent. The floor is what notices. Verified by
        # running the harness against a tree with no fixtures in it: `0 documents, but 3 page(s) say
        # 'more than ninety'`. Do not weaken it into a prose-only assertion; it is carrying two claims.
        claimants = sorted(q for q in ROOT.glob("docs/**/*.md")
                           if CLAIM in q.read_text().lower())
        check("some page still states the suite's size in prose", claimants,
              "the phrase %r is on no page — reword it and FLOOR here together" % CLAIM)
        check("the suite is as large as those pages claim", total >= FLOOR,
              "%d documents, but %d page(s) say %r" % (total, len(claimants), CLAIM))
        for path in claimants:
            print("        %s states it" % path.relative_to(ROOT))

    if broken:
        if failures:
            print("\nthe control worked: pointed at a renderer, the checks above failed")
            sys.exit(0)
        sys.exit("the control FAILED: a command that cannot print an AST was accepted")

    if failures:
        sys.exit("%d failed" % len(failures))
    print("the invitation is a command that works")


if __name__ == "__main__":
    main()
