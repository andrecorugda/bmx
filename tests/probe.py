"""Ask a command whether it is the tool this suite expects, before running the suite against it.

    from probe import speaks

    speaks(command, "ast")    # exits with a diagnosis if it does not answer with a BMX AST
    speaks(command, "page")   # …or with a rendered page

**Every runner here takes a binary path and used to take the WRONG one politely.** The Burxt session
pointed `harness.py` at the compiler instead of the parser it had just built, and got *87 cases, 87
failed*, with the compiler's usage text in every "got". Reproduced here in one command: the report was
87 defects when the fact was one wrong argument.

That is the same shape as a guard I already fixed once, in `tools/check.sh`: it looked for `burxt` on
`PATH`, found a 0.0.153 left behind in a cleaned directory, and reported five failing checks for a
missing standard library. **A check that cannot tell "this is broken" from "you handed me the wrong
thing" sends you to debug the wrong thing**, and it does it confidently, which is worse than saying
nothing.

**One helper, five callers, deliberately.** Five copies of a smoke test is five chances to forget it,
which is the lesson this repository keeps re-learning — nine escape defects that were one recursion, five
separator checks that were one predicate, three consuming loops that wanted one refusal.
"""

import pathlib
import shlex
import subprocess
import sys
import tempfile

# A document every conforming reader must handle, chosen to be the least interesting one possible: if a
# tool cannot answer for this, nothing it says about the other 87 means anything.
TRIVIAL = "hello\n"

WANTS = {
    "ast": ('"type":"document"', 'an AST — JSON whose root is {"type":"document"}'),
    "page": ("<article", "a rendered page — HTML beginning with <article"),
}


def speaks(command, kind):
    """Run `command` on a trivial document and confirm the shape of its answer, or exit explaining."""
    marker, described = WANTS[kind]
    with tempfile.TemporaryDirectory() as tmp:
        doc = pathlib.Path(tmp) / "probe.bmx"
        doc.write_text(TRIVIAL)
        try:
            r = subprocess.run(shlex.split(command) + [str(doc)], capture_output=True, text=True, timeout=60)
        except FileNotFoundError:
            sys.exit(f"cannot run {command!r}: no such command")
        except subprocess.TimeoutExpired:
            sys.exit(f"{command!r} did not answer within 60s on a one-word document")

    out = (r.stdout + r.stderr).replace(" ", "")
    if marker.replace(" ", "") in out:
        return

    # The diagnosis, not just the refusal — the point is to name the likely mistake.
    first = (r.stdout + r.stderr).strip().split("\n")[0][:90] or "(no output)"
    print(f"{command!r} does not answer with {described}.", file=sys.stderr)
    print(f"  it said: {first}", file=sys.stderr)
    if "usage" in out.lower() or "burxt" in out.lower():
        print("  that looks like a COMPILER rather than the program it builds — did you pass `burxt`"
              " where you meant the binary it produced?", file=sys.stderr)
    print("  nothing this suite reports about it would mean anything, so it is stopping here"
          " rather than blaming 87 documents for one wrong argument.", file=sys.stderr)
    sys.exit(2)
