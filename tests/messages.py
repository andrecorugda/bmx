"""Every message either implementation can emit, checked for advice the format no longer accepts.

    python3 tests/messages.py
    python3 tests/messages.py --prove-it     # the negative control

**A message is the compiler talking, so a message that tells you to write something illegal is worse
than a message that says nothing** — you do as you are told, get a second refusal, and the two tools
contradict each other. The star-burxt session shipped four of exactly that today: refusals instructing
the author to write `::: props name: Type` after the fence had been respelled. This repository had none,
and finding that out took two tries.

**Why it reads the SOURCE rather than triggering the refusals.** There are 21 codes across two
implementations and no test exercises all of them; a check that fires only the refusals somebody
remembered is the shape that let star's four through. Reading every message site cannot be selective
about which ones it thinks of.

**And why it scans a WINDOW rather than matching a string literal.** The first version pulled quoted
strings out with a regex and reported *0 of 35 messages mention the old fence* — a zero over incomplete
text, because three of the messages are template literals and the regex captured only up to the first
interpolation. It found one message containing the new fence where three do, which is what gave it away:
**a positive control that finds something is not the same as one that finds everything.** So the scan
anchors on the CALL and reads forward until the parentheses close, which cannot be wrong about a message
form it was never taught.

Two assertions, and the second exists because the first can pass by finding nothing:

- no message mentions a superseded fence
- **at least 30 message sites were found**, per implementation. A guard whose extractor silently stops
  matching reports success over an empty set, which reads exactly like coverage.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (path, what a message site starts with, how many sites are expected at minimum)
SOURCES = [
    ("reference/bmx.js", re.compile(r"new BmxError\(|\bwarn\("), 30),
    ("burxt/bmx.bx", re.compile(r"bmx_error\("), 30),
]

# A superseded spelling, and the pattern that matches the fence by SHAPE. The second is here because
# `grep ':::'` never found the editor config that broke code folding for two releases: it held `:{3,}`.
SUPERSEDED = (":::", ":{3", ":{2,", ":{1,")


def sites(path, opener):
    """Every message site, read from the call to the closing parenthesis."""
    lines = pathlib.Path(ROOT / path).read_text().split("\n")
    out = []
    for i, line in enumerate(lines):
        if not opener.search(line):
            continue
        text, depth = "", 0
        for follow in lines[i:i + 8]:
            text += follow + " "
            depth += follow.count("(") - follow.count(")")
            if depth <= 0 and text.strip():
                break
        out.append((i + 1, " ".join(text.split())))
    return out


def main():
    prove = "--prove-it" in sys.argv
    failures, total = [], 0

    for path, opener, floor in SOURCES:
        found = sites(path, opener)
        total += len(found)

        if prove:
            # The control: a message that instructs the old syntax, in the shape star-burxt shipped.
            found.append((0, """error("BMX-E999", 0, "add `::: props name: Type` at the top")"""))

        for line, text in found:
            for old in SUPERSEDED:
                if old in text:
                    failures.append(f"{path}:{line} instructs a superseded fence: {text[:88]}")
                    break

        if len(found) < floor:
            failures.append(
                f"{path}: only {len(found)} message sites found, expected at least {floor} — "
                "the extractor has stopped matching, so a pass here means nothing")
        else:
            print(f"  {len(found):3} message sites read from {path}")

    for f in failures:
        print(f"  FAIL  {f}")

    if prove:
        if failures:
            print("\nthe control failed as it must — a message instructing the old fence is caught")
            return 0
        print("\nTHE CONTROL DID NOT FAIL, so this check cannot see a bad message")
        return 1

    print(f"\nno message in {total} sites tells an author to write something the format refuses")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
