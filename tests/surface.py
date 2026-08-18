"""Every name the documentation tells a host to call, reached from a real dependent package.

    BURXT_LIB=<lib> python3 tests/surface.py
    BURXT_LIB=<lib> python3 tests/surface.py --prove-it     # the negative control

**Six documented calls, five unreachable.** `docs/` told a host to call `bmx_to_html`, `bmx_bind`,
`bmx_json`, `bmx_html` and `bmx_emit_burxt`, and not one was `public`, so a dependent package could not
reach any of them. Somebody following the documentation writes the call and stops.

**Why nothing caught it: the boundary is the PACKAGE, not the file.** `flag_public` is consulted only
where a declaration carries an owning package, so a non-`public` function called from another *file* in
the same tree compiles happily — which means **no test that stays inside this repository can see the
boundary at all.** `public` had been applied to whatever `burxt/examples/` needed, and those live inside
the package. CI's one consumer test called `bmx_parse`, which is the one name that worked.

star-burxt found the identical defect in its own README the same day — three documented names, none
callable — and named the mechanism. This is their `tools/surface.bx` in Python.

**It checks BOTH directions, and the second is the more dangerous one.** Six functions were `public`,
depended on by star-burxt, and mentioned nowhere in the documentation — so the compatibility promise in
`VERSIONING.md` covered half the surface a consumer was actually using, and any of them could have changed
in a patch release. **Reachable-and-unwritten is worse than written-and-unreachable**: the first breaks a
consumer silently at some later date, the second stops them at the keyboard today.

**The list is derived from the documentation, not maintained here.** A hand-kept list is a second place
to forget a name, and the failure it would hide is precisely the one this file exists to catch: a name
the docs promise and nothing tests.

**And it needs a control for the reason star's did.** Aimed at a name that does not exist, the compiler
answers `unknown function` — a refusal, convincing, and nothing to do with visibility. A renamed helper
would pass forever. So `--prove-it` takes a genuinely private function **discovered from the source**, not
invented, and requires the refusal to say `not \\`public\\`` — which is the only message that means the
boundary was actually consulted.
"""

import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = list((ROOT / "docs").glob("*.md")) + list((ROOT / "docs" / "guide").glob("*.md")) + [ROOT / "README.md"]


# **The two directions need different notions of "documented", and conflating them produced two false
# positives immediately.** Widening the forward check to any mention flagged `bmx_parse_error` — which
# appears inside a QUOTED COMPILER ERROR on the install page — and `bmx_target_allowed`, in a sentence
# describing how BMX implements the scheme rule. Neither is an instruction to call anything.
#
#   forward  (the docs promise it -> a host must be able to reach it):  a promise is a CALL, `name(`
#   reverse  (it is public -> the docs must say so):                    a MENTION is enough

def promised():
    """Every `bmx_*(` the documentation tells a host to CALL. A call is the promise."""
    names = set()
    for page in DOCS:
        names.update(re.findall(r"\b(bmx_[a-z_]+)\(", page.read_text()))
    return sorted(names)


def mentioned():
    """Every `bmx_*` the documentation names at all. Enough to count as written down."""
    names = set()
    for page in DOCS:
        names.update(re.findall(r"\b(bmx_[a-z_]+)", page.read_text()))
    return names


def exported():
    """Every `public` function, which is what a dependent package can actually reach."""
    text = (ROOT / "burxt" / "bmx.bx").read_text()
    return sorted(re.findall(r"^public (?:pure )?function (\w+)\(", text, re.M))


def genuinely_private():
    """A function declared here WITHOUT `public`, read from the source rather than invented.

    An invented name produces `unknown function`, which proves the compiler ran and nothing else.
    """
    text = (ROOT / "burxt" / "bmx.bx").read_text()
    public = set(re.findall(r"^public (?:pure )?function (\w+)\(", text, re.M))
    private = [n for n in re.findall(r"^(?:pure )?function (\w+)\(", text, re.M) if n not in public]
    if not private:
        sys.exit("no non-public function found, so the control has nothing to aim at")
    return private[0]


def reach(name, workdir):
    """Reference `name` from a dependent package and return the compiler's first line."""
    (workdir / "burxt.package").write_text(f"name consumer\nversion 0.1.0\ndependency bmx {ROOT}\n")
    (workdir / "probe.bx").write_text(
        'use "bmx/burxt/bmx.bx";\n'
        f'match {name}("a") {{ Error(e) => {{ print(e); }} Ok(v) => {{ print("ok"); }} }}\n')
    r = subprocess.run(["burxt", "check", "probe.bx"], cwd=workdir, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


def main():
    prove = "--prove-it" in sys.argv
    if not os.environ.get("BURXT_LIB"):
        print("skipped: needs BURXT_LIB and a burxt on PATH")
        return 0

    names = promised()
    if not names:
        print("no documented call matched at all, so the pattern has stopped seeing them")
        return 1

    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        for name in names:
            out = reach(name, work)
            if "not `public`" in out:
                failures += 1
                print(f"  FAIL  {name} is promised by the documentation and is not `public`")
            elif "unknown function" in out:
                failures += 1
                print(f"  FAIL  {name} is promised by the documentation and does not exist")
        print(f"  {len(names)} documented names reached from a dependent package")

        # **The other direction.** A `public` name absent from the documentation is a surface a consumer
        # can already depend on and this project has promised nothing about.
        written = mentioned()
        undocumented = [n for n in exported() if n not in written]
        for n in undocumented:
            failures += 1
            print(f"  FAIL  {n} is `public` — reachable by any host — and appears in no documentation")
        print(f"  {len(exported())} public functions, all of them written down"
              if not undocumented else f"  {len(exported())} public functions")

        if prove:
            hidden = genuinely_private()
            out = reach(hidden, work)
            # The message must name VISIBILITY. Anything else means the control proved the compiler ran.
            if "not `public`" in out:
                print(f"\nthe control failed as it must — `{hidden}` is refused for not being `public`")
                return 0
            print(f"\nTHE CONTROL DID NOT FAIL on `{hidden}`: {out.splitlines()[0][:80] if out else '(no output)'}")
            print("so this check cannot tell a visibility refusal from any other refusal")
            return 1

    if failures:
        print(f"\n{failures} documented name{'' if failures == 1 else 's'} cannot be reached by a host")
        return 1
    print("\nevery name the documentation promises is reachable from another package")
    return 0


if __name__ == "__main__":
    sys.exit(main())
