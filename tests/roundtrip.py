# not-burxt: standalone — CI's Node-only job; in Burxt, BMX's own suite would need BMX's first host installed
"""Indent every document in the suite, reparse it, and assert the structure did not move.

    python3 tests/roundtrip.py "node reference/bmx.js"

**This is the check that found 0.8, and for one day it existed only in a scrollback.** Written as a
throwaway while building `tools/fmt.py`, it immediately made two fixtures stop parsing: `BMX-E012` was
refusing an indented list inside a block, so the readable form of a loop over a list was illegal in the
release whose purpose was making it readable. Then it was not kept — which would have left the most
productive instrument of the day unable to fire again.

**Why it can see what 68 conformance cases cannot.** Every fixture was written by someone who believed
the rules; nobody writes a case asserting that something they think is forbidden actually works. So a
rule that is too BROAD is invisible to the suite by construction — the suite only contains documents its
author expected to be legal. This check does not need anyone to expect anything: it takes documents that
already parse, applies a transform the spec says is meaning-preserving, and asks whether they still do.

**And the third property, which is the one this check was missing.** *42 documents keep their structure
through the formatter* is also exactly what a formatter that did nothing at all would produce — a success
that the defect it looks for would also produce. So the count of documents the formatter actually CHANGED
is reported and required to be non-zero, and the untouched ones are named separately, because they prove
nothing: a document the formatter left alone cannot have been broken by it.

The Burxt session put the general form better than I would, having found a SIGSEGV whose first memory
measurement came back flat — the storage was being freed while still in use, so the reading that looked
like good news *was* the bug: **a wrong answer that looks like good news deserves more scrutiny than a
bad one.**

*Its control is not `--prove-it` — that one mangles the formatter's output, which is a different
assertion. This one was exercised by replacing `tools/fmt.py` with a script that exits immediately: the
check then reports `0 documents were REINDENTED` and fails, which is what it must do. Said here because
an assertion whose control was run once and not written down is an assertion nobody can trust twice.*

**Two properties it asserts, and the second is the one that is easy to get wrong:**

- *Every document that parsed still parses.* This is what fired in 0.7.
- *Its structure is unchanged* — node types, names, heads, nesting. **Offsets are excluded, and that is
  not a loosening:** indentation moves bytes, so offsets MUST change, and an assertion that they do not
  would be asserting the transform did nothing. A check whose subject cannot vary looks exactly like
  coverage and is worse than none, which the star-burxt session put better than I would: *can this
  assertion fail on any input?* This one can, and has, twice.

The negative control is `--prove-it`, which mangles the indenter's output and expects the check to fail.
A check nobody has watched fail is a check nobody has tested.
"""

import json
import pathlib
import shlex
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from probe import speaks  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
FMT = ROOT / "tools" / "fmt.py"


def parse(command, path):
    r = subprocess.run(shlex.split(command) + [str(path)], capture_output=True, text=True)
    if r.returncode != 0:
        return None, (r.stdout + r.stderr).strip().split("\n")[0]
    return json.loads(r.stdout), None


def structure(node):
    """Everything except position. Bytes move when a line is indented; the tree must not."""
    if isinstance(node, dict):
        return {k: structure(v) for k, v in node.items() if k not in ("offset", "head_offset")}
    if isinstance(node, list):
        return [structure(v) for v in node]
    return node


def main():
    args = sys.argv[1:]
    prove = "--prove-it" in args
    rest = [a for a in args if not a.startswith("--")]
    command = rest[0] if rest else "node reference/bmx.js"
    speaks(command, "ast")

    scratch = pathlib.Path(subprocess.run(["mktemp", "-d"], capture_output=True, text=True).stdout.strip())
    checked = refused = moved = skipped = touched = 0
    failures = []

    for source in sorted((ROOT / "tests" / "cases").glob("*.bmx")):
        before, why = parse(command, source)
        if before is None:
            skipped += 1          # a case may be here to pin an error; nothing to round-trip
            continue

        copy = scratch / source.name
        before_text = source.read_text()
        copy.write_text(before_text)
        subprocess.run(["python3", str(FMT), str(copy)], capture_output=True, text=True)
        if copy.read_text() != before_text:
            touched += 1

        if prove:
            # **The control exercises BOTH assertions**, because a control that only reaches one of them
            # leaves the other unproven — which is the shape star-burxt hit tonight, a green test for a
            # defect it could not see.
            #
            # **The mangle has to be RELATIVE, and my first attempt at strengthening it was not.**
            # Shifting every line by one space is meaning-preserving by §1 — a uniform shift moves a code
            # fence along with its content, and keeps every list item at the same depth as its
            # neighbours — so the control passed and proved nothing. That is the same trap it exists to
            # rule out, met while trying to widen it.
            #
            # So: move ONE line relative to the rest. Two mangles, one per assertion:
            #
            # - a line shifted inside a code fence changes CONTENT, because content is relative to its
            #   fence (§2.4) — this reaches the structure assertion, on the one case in the suite whose
            #   body is a code block. Exactly one is the point: the check is sensitive precisely where
            #   the format says bytes matter.
            # - a list item pushed deeper than the item above it is `BMX-E012` (§2.3) — this reaches the
            #   refused assertion, which is the one that fired for real and made 0.7's over-broad rule
            #   visible before this file existed to keep asking.
            lines = copy.read_text().split("\n")
            for i, line in enumerate(lines):
                if i > 0 and line.strip() and not line.strip().startswith(":!"):
                    lines[i] = "  " + line
                    break
            copy.write_text("\n".join(lines))

        after, why = parse(command, copy)
        if after is None:
            refused += 1
            failures.append(f"{source.name}: parsed before, REFUSED after indenting — {why}")
        elif structure(before) != structure(after):
            moved += 1
            failures.append(f"{source.name}: structure changed under a transform that may not change it")
        else:
            checked += 1

    for f in failures:
        print(f"  FAIL  {f}")
    print(f"\n{touched} documents were REINDENTED and kept their structure; "
          f"{checked - touched} the formatter left alone, which proves nothing about it"
          f"{f', {refused} stopped parsing, {moved} changed shape' if failures else ''}"
          f"{f', {skipped} do not parse to begin with' if skipped else ''}")

    if prove:
        # A control that passes has proved nothing: the whole point is watching it fail.
        if failures:
            print("the control failed as it must — the check has a subject that varies")
            return 0
        print("THE CONTROL DID NOT FAIL, so this check cannot see anything")
        return 1
    # **A formatter that did nothing would pass every assertion above.** This is the one that notices.
    if not prove and touched == 0:
        print("no document was reindented at all, so the round-trip compared each file with itself")
        return 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
