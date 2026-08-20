# not-burxt: gap — checks THIS REPOSITORY rather than the format, so the standalone argument never reached it
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

Three assertions, and the third is star-burxt's correction to my second:

- no message mentions a superseded fence
- **two independent extractions agree on the count.** My first version asserted a FLOOR — at least 30
  sites — against real numbers of 35 and 32. Loose enough that a scan silently capturing 30 of 35 would
  pass, which is the same defect as the regex it replaced, one level up: **a floor is a boolean control
  with extra steps.** Two methods required to agree cannot both be wrong in the same direction without
  saying so.
- the count is non-zero, because two extractions that both find nothing agree perfectly.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (path, what a message site starts with)
SOURCES = [
    ("reference/bmx.js", re.compile(r"new BmxError\(|\bwarn\(")),
    ("burxt/bmx.bx", re.compile(r"bmx_error\(")),
]

# A superseded spelling, and the pattern that matches the fence by SHAPE. The second is here because
# `grep ':::'` never found the editor config that broke code folding for two releases: it held `:{3,}`.
SUPERSEDED = (":::", ":{3", ":{2,", ":{1,")


def sites(path, opener):
    """Every message site, read from the call to its balanced close."""
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


def count_by_hand(path, opener):
    """A second, dumber count: how many LINES open a message. Deliberately a different method.

    It exists to disagree. If the reader above starts skipping a message form — the way the regex it
    replaced skipped template literals — these two numbers separate, and the check says so instead of
    reporting a confident zero over two thirds of the messages.
    """
    return sum(1 for line in pathlib.Path(ROOT / path).read_text().split("\n") if opener.search(line))


def main():
    prove = "--prove-it" in sys.argv
    failures, total = [], 0

    for path, opener in SOURCES:
        found = sites(path, opener)
        expected = count_by_hand(path, opener)
        total += len(found)

        if prove:
            # **The control exercises BOTH assertions, one per source**, because a control that only
            # reaches one leaves the other unproven — and the unproven one here is the newer of the two.
            # star-burxt watched theirs fail in both ways it claims to detect; a check whose second
            # assertion has never fired is a claim, not a check.
            if path.endswith(".js"):
                # a message instructing the old syntax, in the shape star actually shipped
                found.append((0, """error("BMX-E999", 0, "add `::: props name: Type` at the top")"""))
            else:
                # a reader that has quietly stopped seeing two thirds of the messages
                found = found[: len(found) // 3]

        for line, text in found:
            for old in SUPERSEDED:
                if old in text:
                    failures.append(f"{path}:{line} instructs a superseded fence: {text[:88]}")
                    break

        # The two extractions must agree, and there must be some. Either alone can pass over a set
        # that has quietly shrunk; together they cannot without disagreeing.
        counted = expected + (1 if prove and path.endswith(".js") else 0)
        if len(found) != counted:
            failures.append(
                f"{path}: the reader found {len(found)} messages and there are {counted} sites — "
                "one method has stopped seeing a form the other can, so nothing here can be believed")
        elif not found:
            failures.append(f"{path}: no message sites at all, which two methods will agree about")
        else:
            print(f"  {len(found):3} message sites read from {path}, and {counted} counted independently")

    for f in failures:
        print(f"  FAIL  {f}")

    if prove:
        # Both kinds, not just one: a bad message caught, AND a shrunken extraction caught.
        instructed = any("instructs a superseded fence" in f for f in failures)
        shrunken = any("one method has stopped seeing" in f for f in failures)
        if instructed and shrunken:
            print("\nthe control failed both ways it must — a bad message, and an extraction gone quiet")
            return 0
        print(f"\nTHE CONTROL IS INCOMPLETE: bad message caught={instructed}, shrunken scan caught={shrunken}")
        return 1
        print("\nTHE CONTROL DID NOT FAIL, so this check cannot see a bad message")
        return 1

    print(f"\nno message in {total} sites tells an author to write something the format refuses")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
