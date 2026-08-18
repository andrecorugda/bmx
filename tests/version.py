"""Every place the documentation states what version BMX is, checked against `SPEC.md`.

    python3 tests/version.py
    python3 tests/version.py --prove-it     # the negative control

**Three status claims were stale at once, and one of them was nine releases behind.** `README.md` said
the format was 0.4, `docs/promise.md` said 0.2, and `docs/building-on.md` listed *"what DOES exist, as of
0.2"* — a capability list frozen before offsets, named closers, insignificant indentation and delimited
heads existed. A framework author reading that page would not have known a one-line block can carry a
body.

**That is the shape star-burxt named and it is worse than an out-of-date number:** nobody re-tests what
they are told is absent. A stale DONE gets found the first time somebody tries the thing; a stale
NOT-DONE is found by nobody, because the reader believes it and leaves.

So the version lives in **one** place — the title of `SPEC.md`, which is the normative document — and
every status claim is checked against it.

**Why it greps patterns rather than a list of files.** A list of known sites cannot see a claim added
somewhere new, which is the failure mode of every registry. The patterns below match how a *status* claim
is phrased; historical references are worded differently on purpose — *"0.6 nested by fence length"*,
*"until 0.5.1"*, *"every version through 0.7"* — and must keep working, so the check would be wrong to
flag them. That distinction is the one thing here a person has to maintain: **if you write a new way of
saying "BMX is version X", add its shape below or the check cannot see it.**
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# How a STATUS claim is phrased. Each must name the current version.
CLAIMS = [
    re.compile(r"BMX is \*{0,2}(\d+\.\d+)"),
    re.compile(r"as of (\d+\.\d+)\b"),
    re.compile(r"target BMX (\d+\.\d+)"),
    re.compile(r"Every construct BMX (\d+\.\d+) has"),
    re.compile(r"^## What (\d+\.\d+) (?:deliberately )?does not have", re.M),
    re.compile(r"^\*\*(\d+\.\d+)\. Two implementations", re.M),
    re.compile(r"which (\d+\.\d+) does not have"),
]

PAGES = ["README.md", "docs/promise.md", "docs/building-on.md", "docs/install.md",
         "docs/syntax.md", "docs/errors.md", "SPEC.md"]


def current():
    """The one place the version is decided: the normative document's title."""
    first = (ROOT / "SPEC.md").read_text().split("\n", 1)[0]
    m = re.search(r"BMX (\d+\.\d+)", first)
    if not m:
        sys.exit("SPEC.md's first line does not name a version, so nothing can be checked against it")
    return m.group(1)


def main():
    prove = "--prove-it" in sys.argv
    want = current()
    print(f"  SPEC.md says the format is {want}")

    stale, checked = [], 0
    for page in PAGES:
        text = (ROOT / page).read_text()
        if prove and page == "README.md":
            # The control: a status claim naming a version that is not the current one. Without it, a
            # check that finds every claim already correct proves only that it ran.
            text += "\n\nBMX is 0.1 and this sentence is the control.\n"
        for pattern in CLAIMS:
            for m in pattern.finditer(text):
                checked += 1
                if m.group(1) != want:
                    line = text[: m.start()].count("\n") + 1
                    stale.append(f"{page}:{line} claims {m.group(1)}, SPEC.md says {want}: {m.group(0)[:60]}")

    for s in stale:
        print(f"  FAIL  {s}")
    print(f"  {checked} status claims checked across {len(PAGES)} pages")

    if prove:
        if stale:
            print("\nthe control failed as it must — a stale status claim is caught")
            return 0
        print("\nTHE CONTROL DID NOT FAIL, so this check cannot see a stale version")
        return 1
    if not checked:
        print("\nno status claim matched at all, which means the patterns have stopped seeing them")
        return 1
    print("\nevery version the documentation states agrees with SPEC.md")
    return 0 if not stale else 1


if __name__ == "__main__":
    sys.exit(main())
