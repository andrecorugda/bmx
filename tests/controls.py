#!/usr/bin/env python3
# not-burxt: standalone — CI's Node-only job; in Burxt, BMX's own suite would need BMX's first host installed
"""Every runner that advertises `--prove-it` actually reads it.

    python3 tests/controls.py
    python3 tests/controls.py --prove-it     # the negative control

**A control that cannot fail reports success forever, and it is the most expensive kind of dead code in a
test suite** — every other check announces its own absence by not being in the output. The star-burxt
session found one in their tree today: a runner whose header advertised `--prove-it` while the flag was a
hardcoded `false`. It ran, printed its success line, and exited 0, having tested nothing about itself.
Nine other controls there were live; that one had never been watched fail.

So: the docstring of a runner is a promise, and this is the one promise no other check can see. `check.sh`
and `ci.yml` run each control once and would notice a control that *crashes* — they cannot notice one that
quietly does nothing, because doing nothing looks exactly like passing.

**Static rather than dynamic, and the reason is a hand-maintained list this would otherwise need.** The
honest dynamic test is *run it twice and require the output to differ*, which is what found the dead one
over there. Here, `tests/surface.py` and anything else needing the Burxt toolchain produces identical
output both ways when the toolchain is absent — so a dynamic check would report a dead control on a
machine with no `burxt`, and telling the two apart needs a list of which runners need what. **A list of
exceptions is the scope this repository keeps getting wrong**, so this asks the narrower question it can
answer everywhere: does the flag reach `argv` at all.

The dynamic half is worth running by hand when a control is added, and the sweep is one line:

    diff <(python3 tests/<r>.py 2>&1) <(python3 tests/<r>.py --prove-it 2>&1)
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
FLAG = "--prove-it"

# How each language reads an argument. A runner may spell it differently; add the spelling rather than
# exempting the file, because an exemption is how a dead control gets to stay.
READS = [
    re.compile(r"sys\.argv"),          # python
    re.compile(r"process\.argv"),      # node
    re.compile(r"\$@|\$1|\$\*"),       # shell
]


def runners():
    for path in sorted(ROOT.rglob("*")):
        if path.suffix not in (".py", ".mjs", ".js", ".sh") or not path.is_file():
            continue
        rel = str(path.relative_to(ROOT))
        if any(s in rel + "/" for s in (".git/", "node_modules/", "editors/vscode/reference/")):
            continue
        yield rel, path


def main():
    prove = FLAG in sys.argv
    advertise, dead = [], []

    for rel, path in runners():
        text = path.read_text()
        if FLAG not in text:
            continue
        # **Advertising means naming the flag in prose, not merely reading it.** A runner that reads the
        # flag and never documents it is not making a promise; one that documents it and never reads it is.
        advertise.append(rel)
        if prove and rel == "tests/portability.py":
            # The control: the defect as star-burxt had it — the flag named in the header, and nothing
            # anywhere that reads an argument. Simulated by stripping the reads from a copy of the text.
            text = "\n".join(l for l in text.splitlines() if not any(r.search(l) for r in READS))
        if not any(r.search(text) for r in READS):
            dead.append(rel)

    for rel in dead:
        print(f"  FAIL  {rel} advertises {FLAG} and never reads an argument — its control cannot fire")
    print(f"  {len(advertise)} runners advertise {FLAG}; {len(advertise) - len(dead)} read an argument")

    if prove:
        if dead:
            print(f"\nthe control failed as it must — an advertised {FLAG} that is never read is caught")
            return 0
        print(f"\nTHE CONTROL DID NOT FAIL, so this check cannot see a dead control")
        return 1
    if not advertise:
        print(f"\nno runner advertises {FLAG} at all, which means this check has stopped seeing them")
        return 1
    if dead:
        return 1
    print(f"\nevery advertised control reads its flag")
    return 0


if __name__ == "__main__":
    sys.exit(main())
