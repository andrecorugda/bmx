#!/usr/bin/env python3
"""Two renderers, one page — do they agree?

`tests/harness.py` asks whether an implementation parses to the right tree. This asks the level-1
question the tree cannot: **does it produce the same page?** Two implementations can agree on every
AST in the corpus and still disagree about what to do with it — a different heading tag, a different
escape set, a link scheme one allows and the other refuses.

It exists because the claim came before the code. `README.md` listed `reference/bmx.js` as
"1 — renders" while that file exported only `parse`, and `BOUNDARY.md` defines level 1 as parsing
*and* substituting slot values with escaping applied. So the table described a level the reference
implementation had not reached — and "any language can reach level 1" is the sentence that makes BMX
adoptable, with the reference implementation as its proof.

    python3 tests/renders.py <burxt-render-command>

where the command is a program that prints a rendered page for one document, e.g. the build of
`tools/render.bx`. Both sides are given the same bindings, which are the ones that tool declares.

Exits non-zero on the first page that differs.
"""

import pathlib
import shlex
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent

# The bindings `tools/render.bx` declares. Both renderers must be handed the same ones, or this
# compares two different questions.
BINDINGS = {
    "name": "Ada",
    "customer.name": "Ada Lovelace",
    "order.reference": "R-4417",
    "order.total": "$59.97",
    "order.delivery": "Thursday",
    "order.paid_at": "16 August",
}

JS = """
import { render, BmxError } from '%s'
import { readFileSync } from 'node:fs'
const bindings = %s
try {
  process.stdout.write(render(readFileSync(process.argv[2], 'utf8'), bindings) + '\\n')
} catch (e) {
  process.stdout.write((e instanceof BmxError ? e.message : String(e)) + '\\n')
}
"""


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    burxt = shlex.split(sys.argv[1])

    import json
    runner = HERE / ".renders.mjs"
    runner.write_text(JS % ((ROOT / "reference" / "bmx.js").as_uri(), json.dumps(BINDINGS)))

    documents = sorted((HERE / "cases").glob("*.bmx"))
    same, differ, refused = 0, [], 0
    for doc in documents:
        js = subprocess.run(["node", str(runner), str(doc)], capture_output=True, text=True).stdout.strip()
        bx = subprocess.run(burxt + [str(doc)], capture_output=True, text=True).stdout.strip()
        # **A page both refuse is agreement, and it is the interesting kind.** The corpus is full of
        # documents this renderer must decline — a block it did not declare, a `javascript:` target —
        # and two implementations refusing the same document for the same reason is exactly what
        # level 1 means. Compared on the code, because the prose after it is each host's own.
        if js.startswith("BMX-R") and bx.startswith("BMX-R"):
            if js.split(":")[0] == bx.split(":")[0]:
                refused += 1
                continue
        if js == bx:
            same += 1
        else:
            differ.append((doc.name, js, bx))

    runner.unlink(missing_ok=True)

    # `tests/errors/` is deliberately not here: those documents do not parse, so there is no page
    # to compare. Saying the number out loud keeps "36" from reading like a suite that lost 22.
    print(f"{len(documents)} valid documents in tests/cases: {same} rendered identically, "
          f"{refused} refused by both with the same code")
    print("(tests/errors/ holds 22 more that do not parse — nothing to render)")
    if differ:
        for name, js, bx in differ[:5]:
            print(f"\n  DIFFER {name}")
            print(f"    reference: {js[:200]}")
            print(f"    burxt:     {bx[:200]}")
        print(f"\n{len(differ)} differ")
        sys.exit(1)
    print("the two renderers agree on every document")


if __name__ == "__main__":
    main()
