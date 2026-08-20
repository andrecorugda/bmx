# not-burxt: gap — checks THIS REPOSITORY rather than the format, so the standalone argument never reached it
"""The reference parser's runtime floor, read out of the documentation and checked against the source.

    python3 tests/portability.py
    python3 tests/portability.py --prove-it     # the negative control

**A zero-dependency parser whose runtime requirement is undocumented is not portable — it is untested on
everything except the machine that wrote it.** `reference/bmx.js` is the implementation this project offers
a stranger to copy, and until now nothing said which Node runs it. CI provides Node 20, which is a *pin*
and was never a floor: the two numbers are different, and conflating them is what makes a host upgrade for
a reason that is not theirs.

**Measured, not chosen.** The newest thing the file uses is nullish coalescing, so the floor is Node 14.
The check derives that number from `docs/install.md` rather than holding its own copy, because a floor
stated in two places is a floor that goes stale in one of them.

**And measuring it produced a false positive first, which is the reason this file scans the way it does.**
A pattern of `\\.at\\(` reported `Array.prototype.at` and a floor of Node 16.6 — from line 984, which is
`...at(source, offset)`: a **spread of a local function named `at`**, where the third dot of `...` matched
the `.`. I nearly documented a floor 2.6 versions too high on the strength of it. So:

- comments and string literals are stripped before anything is matched, because a feature *named in prose*
  is not a feature *used*
- the member-access patterns require a real receiver before the dot

**What this cannot see**, said out loud because a check that overstates its reach is worse than none: it
knows the features listed below and nothing else. A file that starts using `Object.groupBy` (Node 21) is
caught; one that uses a Node API rather than a language feature is not. The list is the maintained part.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = "reference/bmx.js"
FLOOR_DOC = "docs/install.md"

# (pattern, name, the Node release that first shipped it)
# **An empty feature table reports the best possible answer.** Proven by emptying it: *"needs nothing
# newer than Node 0, and the documentation promises 14"*, exit 0. A check whose whole job is measuring a
# floor reports maximum portability when it measures nothing — and the ways to get there are ordinary: a
# regex that stops matching after a source reformat, or this list edited down. So `main` asserts the table
# is populated and that something in it was actually found. Same shape as the star-burxt session's gate
# that printed `every guarantee holds` with no count.
FEATURES = [
    (r"\bObject\.groupBy\(",                            "Object.groupBy",            21.0),
    (r"\bArray\.fromAsync\(",                           "Array.fromAsync",           22.0),
    (r"\bstructuredClone\(",                            "structuredClone",           17.0),
    (r"\bObject\.hasOwn\(",                             "Object.hasOwn",             16.9),
    (r"[\w\)\]](?<!\.)\.at\(",                          "Array/String.at",           16.6),
    (r"\.replaceAll\(",                                 "String.replaceAll",         15.0),
    (r"\?\?=|\|\|=|&&=",                                "logical assignment",        15.0),
    (r"\?\?",                                           "nullish coalescing",        14.0),
    (r"\?\.",                                           "optional chaining",         14.0),
    (r"\bmatchAll\(",                                   "String.matchAll",           12.0),
    (r"\.flatMap\(|\.flat\(",                           "Array.flat / flatMap",      11.0),
    (r"\bpadStart\(|\bpadEnd\(",                        "String.padStart / padEnd",   8.0),
]


def strip(src):
    """Comments and string literals out, so a feature mentioned in prose is not a feature used."""
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`(?:\\.|[^`\\])*`", "''", src)


def stated_floor():
    """The floor as the documentation states it. One place, so it cannot go stale in the other."""
    text = (ROOT / FLOOR_DOC).read_text()
    m = re.search(r"\*\*Node (\d+(?:\.\d+)?) or newer\*\*", text)
    if not m:
        sys.exit(f"{FLOOR_DOC} does not state a Node floor, so there is nothing to check against")
    return float(m.group(1))


FEATURE_FLOOR = 8        # far below the twelve it knows; the assertion is "a table exists", not a budget


def main():
    prove = "--prove-it" in sys.argv
    floor = stated_floor()
    src = strip((ROOT / SOURCE).read_text())
    if prove:
        # The control is a real feature that really would break the stated floor, in the real shape.
        src += "\nconst copy = structuredClone(tree)\n"

    # The table and the scan must both have found something — see the note above `FEATURES`.
    if len(FEATURES) < FEATURE_FLOOR:
        sys.exit(f"the feature table holds {len(FEATURES)} patterns, below the floor of {FEATURE_FLOOR} "
                 f"— it has been edited down, and an empty table measures every file as Node 0")

    used = []
    for pattern, name, since in FEATURES:
        m = re.search(pattern, src)
        if m:
            used.append((since, name, src[:m.start()].count("\n") + 1))
    used.sort(reverse=True)

    if not used:
        sys.exit(f"no known feature matched {SOURCE} at all, so the measured floor is meaningless — "
                 f"the patterns have stopped matching, which reports maximum portability")

    print(f"  {FLOOR_DOC} states a floor of Node {floor:g}")
    for since, name, line in used[:4]:
        mark = "  <-- above the floor" if since > floor else ""
        print(f"    Node {since:>5g}   {name:26s} line {line}{mark}")

    over = [(s, n, l) for s, n, l in used if s > floor]
    print()
    if prove:
        if over:
            print("the control failed as it must — a feature above the stated floor is caught")
            return 0
        print("THE CONTROL DID NOT FAIL, so this check cannot see the floor being raised")
        return 1
    if over:
        for since, name, line in over:
            print(f"  FAIL  {SOURCE}:{line} uses {name}, which needs Node {since:g} — above the "
                  f"documented floor of {floor:g}. Either replace it or raise the number in {FLOOR_DOC}, "
                  f"and if you raise it, say what a consumer gains for the upgrade")
        return 1
    highest = used[0][0] if used else 0
    print(f"{SOURCE} needs nothing newer than Node {highest:g}, and the documentation promises {floor:g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
