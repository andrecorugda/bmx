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

**Two questions, because the star-burxt session's dead control had a signature the first one misses.**
Theirs read its flag correctly and `check-all.sh` never passed it — it ran the tool and not the tool
`--prove-it`. **A live control the suite never invokes is exactly as dead as one that ignores its flag**,
and either question alone names only half the class. So this also asserts that `tools/check.sh` runs each
control with the flag.

**And *offering* a control is not *mentioning* one.** The first version of this file matched the flag
anywhere in a file, which counted `tools/check.sh` itself — a script that passes `--prove-it` to eleven
other runners and offers none. It then "passed" that question because `run()` reads `$1`. Using versus
mentioning, in the check written the same day as three other instances of it. So advertising is
**positional**: the flag must appear in the file's own usage block, the first 20 lines, which is where a
runner documents how to run itself and where an invocation of somebody else never is.
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


CHECK_SH = "tools/check.sh"
PATHLIKE = re.compile(r"[\w./-]+\.(?:py|mjs|js|sh)")


def offers(rel, path):
    """Does this file document a control of its OWN, rather than invoke somebody else's?

    **By whose name is on the line, not by where the line is.** The first rule here was positional — the
    flag inside the first 20 lines — and it dropped `tests/roundtrip.py`, whose usage block sits below a
    longer docstring and first names the flag on line 29. **A window tight enough to exclude
    `tools/check.sh` was tight enough to exclude a real control**, which is the same silent loss of
    coverage as the marker rule matching a mention, one direction over: too loose counts what it should
    not, too tight stops counting what it should.

    So: a line carrying the flag offers a control when it names *this* file, or names no file at all. Every
    such line in `check.sh` names one of eleven other runners, and never itself.
    """
    own = rel.rsplit("/", 1)[-1]
    for line in path.read_text().splitlines():
        if FLAG not in line:
            continue
        named = PATHLIKE.findall(line)
        if not named or any(n.endswith(own) for n in named):
            return True
    return False


def main():
    prove = FLAG in sys.argv
    advertise, dead, unrun = [], [], []
    runner = (ROOT / CHECK_SH).read_text().splitlines()

    for rel, path in runners():
        text = path.read_text()
        if not offers(rel, path):
            continue
        # **Advertising means naming the flag in prose, not merely reading it.** A runner that reads the
        # flag and never documents it is not making a promise; one that documents it and never reads it is.
        advertise.append(rel)

        # The second question: does anything actually pass it? One line must name both the file and the
        # flag — which is how `check.sh` writes every one of them, including the two that take an
        # argument first.
        named = any(rel in line and FLAG in line for line in runner)
        if prove and rel == "tests/version.py":
            named = False
        if not named:
            unrun.append(rel)
        if prove and rel == "tests/portability.py":
            # The control: the defect as star-burxt had it — the flag named in the header, and nothing
            # anywhere that reads an argument. Simulated by stripping the reads from a copy of the text.
            text = "\n".join(l for l in text.splitlines() if not any(r.search(l) for r in READS))
        if not any(r.search(text) for r in READS):
            dead.append(rel)

    for rel in dead:
        print(f"  FAIL  {rel} advertises {FLAG} and never reads an argument — its control cannot fire")
    for rel in unrun:
        print(f"  FAIL  {rel} offers a control and {CHECK_SH} never passes {FLAG} — nothing ever fires it")
    print(f"  {len(advertise)} runners offer {FLAG}; {len(advertise) - len(dead)} read an argument "
          f"and {len(advertise) - len(unrun)} are run with it")

    if prove:
        if dead or unrun:
            print(f"\nthe control failed as it must — an advertised {FLAG} that is never read is caught")
            return 0
        print(f"\nTHE CONTROL DID NOT FAIL, so this check cannot see a dead control")
        return 1
    if not advertise:
        print(f"\nno runner advertises {FLAG} at all, which means this check has stopped seeing them")
        return 1
    if dead or unrun:
        return 1
    print(f"\nevery offered control reads its flag and is run with it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
