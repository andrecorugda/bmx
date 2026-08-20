#!/usr/bin/env python3
# not-burxt: gap — checks THIS REPOSITORY rather than the format, so the standalone argument never reached it
"""Every file in this repository that is not Burxt says why it is not.

    python3 tests/languages.py
    python3 tests/languages.py --prove-it     # the negative control

**Andre's rule for all three projects: if it can be written in Burxt, it must be, and reaching for
another language is a gap report rather than a solution.** BMX is the furthest of the three from that
rule by raw count — 6,367 non-Burxt lines against 1,967 of Burxt — and it also has the strongest
defence, which is exactly why the defence has to be written down per file instead of argued once. A
count on its own reads worse than the truth; a count with a reason beside every line is an audit.

The star-burxt session raised it after failing the rule itself: told that `reference/bmx.js` exports
`render`, they imported 1,171 lines of JavaScript into a product whose argument is that you do not need
any, while `bmx_to_html` sat in `burxt/bmx.bx` already conformance-tested. Their amendment is worth
keeping: *do not reimplement* is right, and *import the implementation in the host's own language when
one exists* is stronger.

**Five defences, and only the first two are about BMX being a format rather than a program:**

`reference`   The reference implementation is JavaScript ON PURPOSE. The format's central claim is that
              any language can implement it; a reference written in the host language would make that
              claim untestable by anyone who does not have the host. This is the same reason
              `harness.py` is deliberately not part of the specification.
`neutral`     A runner that takes an arbitrary implementation command. If it were Burxt, running the
              conformance suite would require the Burxt toolchain — so a stranger implementing BMX in
              a sixth language could not check their work, which is the one thing these files exist
              for.
`bootstrap`   `tools/check.sh` only. The entry point a contributor runs **before** any toolchain
              exists, so it cannot need what it installs — the chicken-and-egg category, and it
              already discloses which groups it skipped.
`platform`    The artefact under test, or the runtime it runs in, is JavaScript and nothing else can
              be: VS Code's extension host is Node, a TextMate grammar is tokenised by a JS engine,
              and `docs/assets/code.js` runs in the reader's browser.
`vendored`    A byte copy of a file from burxt-lang.org. `docs/_config.yml` says re-copy rather than
              edit, so it carries no marker and is named here instead — editing it to add one would
              break the property that makes it a copy.
`gap`         **Could be Burxt and is not.** Named rather than defended. This is the number the rule
              is about, and it is the only category that should ever shrink.

**`standalone` used to be a category here and it was doing work it had not earned.** It covered sixteen
files on the strength of `ci.yml`'s sentence — *the format must be testable without its first host
installed* — and **that sentence is about the format, not about this repository's CI.** What the format's
claim actually needs is the fixtures, which are data, plus a runner a stranger can execute: that is
`neutral`, and it is genuinely permanent. `tests/version.py`, `tests/branding.py`,
`editors/vscode/pack.py` and the rest check *this repository*. In Burxt they would make the conformance
job need a toolchain — which costs a contributor without one some checks, and **costs the format's
portability claim nothing at all.**

Conflating those two is how a real property lent its authority to a choice. Reclassified 2026-08-21:
fifteen files moved to `gap`, and the gap went from 708 lines to 3,074. **The number was wrong in the
flattering direction, which is the only direction that survives.**

**This total is not comparable to the other repositories', and that has to be said here or a reader will
compare it anyway.** star-burxt reached `gap` zero; BMX cannot and should not. The difference is
structural rather than a difference in effort: **`ci.yml`'s conformance job may not need a Burxt
toolchain**, by a design decision older than this check — the format must be testable without its first
host installed — and star has no equivalent job, so it has no equivalent constraint. That single property
makes `reference`, `neutral` and `standalone` **permanent** non-Burxt code here — a release cannot unforbid
them and no amount of work should remove them.

**The subtotal is printed rather than written here.** The first draft of this paragraph stated it as
3,871 lines; it was 3,911, and the arithmetic was mine rather than measured. A number in a docstring is a
claim with no runner behind it, which is the defect this repository spends its checks converting.

So the honest reading of these numbers is: `gap` is the debt, and the rest is the architecture. A
different repository's zero and this one's remainder are not measuring the same thing. The star-burxt
session put it better than I did — *"your standalone property generates permanent non-Burxt code and star
has no equivalent, so BMX's remainder is not debt"* — and asked that it be written where the number is
printed rather than left to inference.

**The marker must be a DECLARATION, not a mention** — beginning a comment line, inside the file's
first 20 lines, with its reason free to follow on the same line. `tests/version.py` learned that the hard way the same day: its opt-out marker was matched
anywhere in a file, so `CLAUDE.md` opted itself out of the version gate by *describing* how opting out
works, and the page count fell silently. A file can be removed from a check by writing prose about the
check, so this one is positional.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUFFIXES = (".py", ".mjs", ".js", ".sh")
# The category, then optionally a human explanation after it. **Anchored to the START of a comment
# line**, which is what keeps this a declaration rather than a mention: prose referring to a marker
# has words before it, so `add \`not-burxt: <reason>\`` in the message below cannot match itself.
# The first draft anchored `$` immediately after the category and matched nothing but this very file,
# because every marker written carries its reason after an em dash — a predicate that only accepted
# the bare form, in a repository whose convention is that a marker explains itself.
MARKER = re.compile(r"^(?:#|//)\s*not-burxt:\s*([a-z]+)(?:\s|$)")
WITHIN = 20

REASONS = ("reference", "neutral", "bootstrap", "platform", "gap")

# Files that must not be edited, so they cannot carry a marker. The reason lives here because the
# alternative is editing the thing whose whole property is being an unedited copy.
VENDORED = {"docs/assets/site.js": "a byte copy of burxt-lang.org's, per docs/_config.yml"}

# Never scanned: git's own, installed dependencies, and the parser copy `pack.py` stages into the
# extension (gitignored, and counting it is what made an outside audit read 8,125 where the tree has
# 6,367 — the same 1,171 lines twice).
SKIP = (".git/", "node_modules/", "editors/vscode/reference/")


def sources():
    for path in sorted(ROOT.rglob("*")):
        if path.suffix not in SUFFIXES or not path.is_file():
            continue
        rel = str(path.relative_to(ROOT))
        if any(s in rel + "/" for s in SKIP):
            continue
        yield rel, path


def declared(path):
    """The reason a file declares, as a declaration: alone on its line, near the top."""
    for line in path.read_text().splitlines()[:WITHIN]:
        m = MARKER.match(line.strip())
        if m:
            return m.group(1)
    return None


def main():
    prove = "--prove-it" in sys.argv
    missing, unknown, tally, gaps = [], [], {}, []

    for rel, path in sources():
        if rel in VENDORED:
            reason = "vendored"
        else:
            reason = declared(path)
        if prove and rel == "tests/harness.py":
            # The control is a real file with its marker taken away — the defect as it would happen,
            # somebody adding a runner and not saying why it is not Burxt.
            reason = None
        if reason is None:
            missing.append(rel)
            continue
        if reason not in REASONS + ("vendored",):
            unknown.append(f"{rel}: {reason!r}")
            continue
        lines = len(path.read_text().splitlines())
        tally[reason] = tally.get(reason, 0) + lines
        if reason == "gap":
            gaps.append((rel, lines))

    for rel in missing:
        print(f"  FAIL  {rel} does not say why it is not Burxt — add `not-burxt: <reason>` in its "
              f"first {WITHIN} lines")
    for u in unknown:
        print(f"  FAIL  {u} is not one of {REASONS}")

    burxt = sum(len(p.read_text().splitlines()) for p in ROOT.rglob("*.bx"))
    total = sum(tally.values())
    print(f"  {burxt} lines of Burxt; {total} not, every one of them accounted for:")
    for reason in REASONS + ("vendored",):
        if reason in tally:
            print(f"    {tally[reason]:>5}  {reason}")

    # Printed, not asserted, for the reason in the docstring: `gap` is the debt and the rest is the
    # architecture, so the two want reading differently rather than summing.
    permanent = sum(tally.get(r, 0) for r in ("reference", "neutral", "platform"))
    print(f"  of that, {permanent} lines are permanent — reference, neutral and platform, which no")
    print(f"  release and no amount of work can move; everything in `gap` can.")

    # **The gap total is printed rather than capped.** A threshold here would be a number somebody
    # raises when it is inconvenient, and the rule is not "keep it under N" — it is "know what it is".
    if gaps:
        print("  the gap, named:")
        for rel, lines in sorted(gaps, key=lambda g: -g[1]):
            print(f"    {lines:>5}  {rel}")

    # **Zero is not a passing count, and this printed its success line over nothing.** Proven by handing
    # it an empty scan: *"0 lines not Burxt, every one of them accounted for"*, exit 0. A glob that stops
    # matching — a renamed directory, a suffix dropped from the list — reads exactly like a tree with
    # nothing left to explain. The star-burxt session found the same shape in the most important suite
    # they have: `every guarantee holds`, no number, which is what it would print over zero guarantees.
    #
    # The floors are deliberately far below today's numbers. They are not budgets; they are the assertion
    # that the scan found a tree at all.
    if burxt < 500 or total < 500:
        print(f"  FAIL  this scanned {burxt} lines of Burxt and {total} of anything else, which is not "
              f"this repository — the glob has stopped finding it")
        missing = missing or ["(the scan itself)"]

    if prove:
        if missing or unknown:
            print("\nthe control failed as it must — a file with no stated reason is caught")
            return 0
        print("\nTHE CONTROL DID NOT FAIL, so this check cannot see an unexplained language choice")
        return 1
    if missing or unknown:
        print(f"\n{len(missing) + len(unknown)} file(s) do not account for their language")
        return 1
    print("\nevery non-Burxt file says why")
    return 0


if __name__ == "__main__":
    sys.exit(main())
