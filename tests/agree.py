#!/usr/bin/env python3
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
