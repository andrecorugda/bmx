#!/usr/bin/env python3
# not-burxt: neutral — takes an arbitrary implementation command — in Burxt, nobody without the toolchain could run it
"""Check that two BMX implementations agree — on documents nobody wrote a case for.

    python3 tests/agree.py '<command A>' '<command B>' [directory]

Both commands are run over every `.bmx` file in the directory (default: `tests/cases` and
`tests/errors`). Success must produce the same AST; failure must produce the same error CODE.
The message after the code is each implementation's own words and is not compared.

**Why this exists, separately from `harness.py`.** The conformance suite asks "does this
implementation match what we wrote down". This asks the harder question: *do two implementations
that were written independently reach the same answer where nothing was written down?* Those come
apart exactly where a specification is ambiguous — and a suite cannot find its own blind spots,
because it is made of them.

This is the discipline Burxt applies to itself, pointed at a format: two compilers whose output
must be byte-identical, so a disagreement is a bug report rather than a preference.

**A blind spot in the corpus, written down because it has already produced a real divergence.** No
fixture contains a CONTROL BYTE, and `SPEC.md` §1 makes one legal: a document is a sequence of bytes and
UTF-8 passes through unexamined. Measured 2026-08-21 on `a\x01b`:

    reference/bmx.js   {"type":"text","value":"a\u0001b"}     valid JSON
    burxt/bmx.bx       the byte emitted raw                    INVALID JSON — Python's json rejects it

and on `a\x00b` the Burxt output is additionally **truncated mid-string**, because a Burxt String can
hold a zero byte (`len` counts it) while printing stops at it. Both are in Burxt's `std/json.bx`:
`json_escape` escapes `"` `\` `\n` `\r` `\t` `\b` `\f` and leaves every other byte below 0x20 raw,
which RFC 8259 §7 forbids. **Reported upstream; not added as a fixture yet**, because a case this suite
cannot pass would make CI red for a reason that is not this repository's — the same argument `ci.yml`
makes about never building Burxt from a branch. It becomes a case the moment a release escapes them.

**Its limit, stated because it would otherwise be overclaimed:** agreement between two
implementations written by the same author is weaker evidence than agreement between two written
by strangers. It catches drift and regression; it does not prove the spec unambiguous. Only a
third-party implementation does that, and BMX does not have one yet — see VERSIONING.md on what
1.0 requires.
"""
import json
import pathlib
import shlex
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from probe import speaks  # noqa: E402

HERE = pathlib.Path(__file__).parent


def run(command, path):
    result = subprocess.run(shlex.split(command) + [str(path)], capture_output=True, text=True)
    if result.returncode == 0:
        try:
            return ("ast", json.dumps(json.loads(result.stdout), sort_keys=True))
        except json.JSONDecodeError:
            return ("broken", result.stdout.strip())
    said = (result.stderr or result.stdout).strip()
    return ("error", said.split(" ", 1)[0])


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    a, b = sys.argv[1], sys.argv[2]
    speaks(a, "ast")
    speaks(b, "ast")
    roots = [pathlib.Path(sys.argv[3])] if len(sys.argv) == 4 else [HERE / "cases", HERE / "errors"]

    documents = sorted(p for root in roots for p in root.glob("*.bmx"))
    if not documents:
        sys.exit("no .bmx documents found — refusing to report agreement over nothing")

    disagreements = []
    for path in documents:
        left, right = run(a, path), run(b, path)
        if left != right:
            disagreements.append("%s\n  A %s %s\n  B %s %s" % (path.name, *left, *right))

    for line in disagreements:
        print(line)
    print("%d documents, %d agree, %d differ"
          % (len(documents), len(documents) - len(disagreements), len(disagreements)))
    sys.exit(1 if disagreements else 0)


if __name__ == "__main__":
    main()
