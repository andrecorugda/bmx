"""Every place the documentation states what version BMX is, checked against `SPEC.md`.

    python3 tests/version.py
    python3 tests/version.py --prove-it     # the negative control

**Three status claims were stale at once, and one of them was nine releases behind.** `README.md` said
the format was 0.4, `docs/promise.md` said 0.2, and `docs/building-on.md` listed *"what DOES exist, as of
0.2"* — a capability list frozen before offsets, named closers, insignificant indentation and delimited
heads existed. A framework author reading that page would not have known a one-line block can carry a
body.

**That is the shape star-burxt named and it is worse than an out-of-date number:** nobody re-tests what
they are told is absent. A stale DONE gets found the first time somebody tries the thing; a stale
NOT-DONE is found by nobody, because the reader believes it and leaves.

So the version lives in **one** place — the title of `SPEC.md`, which is the normative document — and
every status claim is checked against it.

**Why it greps patterns rather than a list of files.** A list of known sites cannot see a claim added
somewhere new, which is the failure mode of every registry. The patterns below match how a *status* claim
is phrased; historical references are worded differently on purpose — *"0.6 nested by fence length"*,
*"until 0.5.1"*, *"every version through 0.7"* — and must keep working, so the check would be wrong to
flag them. That distinction is the one thing here a person has to maintain: **if you write a new way of
saying "BMX is version X", add its shape below or the check cannot see it.**
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# How a STATUS claim is phrased. Each must name the current version.
CLAIMS = [
    re.compile(r"BMX is \*{0,2}(\d+\.\d+)"),
    re.compile(r"as of (\d+\.\d+)\b"),
    re.compile(r"target BMX (\d+\.\d+)"),
    re.compile(r"Every construct BMX (\d+\.\d+) has"),
    re.compile(r"^## What (\d+\.\d+) (?:deliberately )?does not have", re.M),
    re.compile(r"^\*\*(\d+\.\d+)\. Two implementations", re.M),
    re.compile(r"which (\d+\.\d+) does not have"),
    re.compile(r"^BMX (\d+\.\d+) — a format of", re.M),      # the site footer, hard-coded
    re.compile(r"^bmx_version: \"(\d+\.\d+)\"", re.M),        # and the variable that replaced it
]

# **This was a hand-written list of six pages, and a new page escaped it in silence.** `docs/implementing.md`
# was added carrying "BMX is 0.12"; the phrasing matched the first pattern above perfectly, and the check
# still passed with `0.11` written on it, because the file was not on the list. **That is the registry
# failure mode this file's own docstring names two paragraphs up** — *"a list of known sites cannot see a
# claim added somewhere new"* — and it was written about the PATTERNS while the FILES sat in a literal
# list underneath. A rule applied to one half of a check and not the other. Globbing it caught
# `docs/index.md` claiming 0.4 on the landing page, eight minors stale and the most-viewed claim on the site.
#
# **So every `.md` in the tree is read, and the one exception lives in the file it describes rather than
# here.** `VERSIONING.md` is the changelog: it says *"a host may be at 3.0 and target BMX 0.1"* as an
# illustration and quotes *"as of 0.2"* as a mistake it is writing up, both of which match the shapes above
# and neither of which is a status claim. Excluding it by name would rebuild the list one exception at a
# time — which is the thing being removed — so a file opts out with a marker IN ITSELF, and a future
# changelog declares itself instead of being remembered here. The star-burxt session hit the same fork in
# its own `.vsix` check today and took the same turn: fix the collision, do not grow the exception.
OPT_OUT = "<!-- version-claims: historical -->"

# **A DECLARATION, not a mention — and the difference was found by this check quietly losing a file.**
# The first version tested `OPT_OUT in text`, so `CLAUDE.md` opted itself out the moment it *described*
# the marker in a sentence about how the opt-out works. The page count fell 25 → 24 and nothing said so;
# it was noticed only because the number was read. **A file can be dropped from a check by writing prose
# about the check**, which is the same shape as a gate reading its own control literal — the star-burxt
# session hit that in their `.vsix` check the same day, and I had flagged the family to them an hour
# before writing this bug.
#
# So the marker must be alone on its line and in the file's header, where a declaration lives. A sentence
# quoting it, a table describing it, or a fenced example showing it are all mentions and stay in scope.
OPT_OUT_WITHIN = 20


def opts_out(text):
    return any(line.strip() == OPT_OUT for line in text.splitlines()[:OPT_OUT_WITHIN])

# The two non-`.md` files a glob for prose cannot reach. **The footer said "BMX 0.2" on every page of the
# site, six minors stale**, and it was invisible here twice over: this list held only `.md` files, and
# `BMX 0.2 —` matches none of the shapes above. The version is `site.bmx_version` now, checked below — and
# the layout is scanned so a hard-coded one added later is caught. **The most-viewed claim on the site was
# the last one checked, because a template is not a document.**
TEMPLATES = ["docs/_layouts/default.html", "docs/_config.yml"]


def pages():
    """Every prose file in the tree, minus the ones that declare themselves historical."""
    found = []
    for path in sorted(ROOT.glob("**/*.md")):
        if any(part in (".git", "node_modules") for part in path.parts):
            continue
        if opts_out(path.read_text()):
            continue
        found.append(str(path.relative_to(ROOT)))
    return found + TEMPLATES


PAGES = pages()


# **`burxt.package`'s version is checked on its own rather than as a CLAIMS pattern, and the reason is a
# false positive I nearly shipped.** The obvious pattern is `^version\s+(\d+\.\d+)` — and
# `docs/install.md` shows a *consumer's* manifest, `name my-app` / `version 0.1.0`, which that pattern
# reads as a stale BMX claim. It is somebody else's version, in an example, and flagging it would be the
# `\.at\(` mistake this file's docstring already records: a shape that matches text which is not the
# thing. So the manifest is read by path, and the patterns above stay for prose.
#
# It compares major.minor, because the manifest carries a patch (`0.12.2`) and `SPEC.md`'s title does not.
# That is the same rule `tests/extension.py` applies to the extension, for the same reason: a packaging
# fix must not need a format release.
MANIFEST = "burxt.package"


def manifest_version():
    """The version `burxt.package` declares, as major.minor — or None if there is no manifest."""
    path = ROOT / MANIFEST
    if not path.is_file():
        return None
    m = re.search(r"^version\s+(\d+\.\d+)", path.read_text(), re.M)
    return m.group(1) if m else "(no version line)"


def current():
    """The one place the version is decided: the normative document's title."""
    first = (ROOT / "SPEC.md").read_text().split("\n", 1)[0]
    m = re.search(r"BMX (\d+\.\d+)", first)
    if not m:
        sys.exit("SPEC.md's first line does not name a version, so nothing can be checked against it")
    return m.group(1)


def main():
    prove = "--prove-it" in sys.argv
    want = current()
    print(f"  SPEC.md says the format is {want}")

    stale, checked = [], 0

    # The manifest, before the prose: a consumer FETCHES it, so it travels further than any page here.
    # **Not "a consumer's tool reads it", which is what this comment said first.** I had asserted that
    # `burxt review --semver` reads a declared version; verified in Burxt's tree, it does not — two source
    # paths and a `--require` operand, no manifest anywhere in `review.rs`. Inferred from the command's
    # name. The check is still worth having for the reason below, which does not need a tool to exist.
    # **Appended to `stale` rather than printed on its own**, because printing a FAIL that does not reach
    # the exit code is the lying-summary defect recorded at the bottom of this very file. Written that way
    # first, in the file carrying the comment about it.
    declared = manifest_version()
    if prove and declared is not None:
        declared = "0.1"
    if declared is None:
        print(f"  --    no {MANIFEST}, so nothing declares a package version")
    elif declared == want:
        checked += 1
        print(f"  ok    {MANIFEST} declares {declared}, which is SPEC.md's")
    else:
        checked += 1
        stale.append(f"{MANIFEST} declares {declared}, SPEC.md says {want} — "
                     f"a consumer fetches this file, so it is the claim with the widest reach")
    for page in PAGES:
        text = (ROOT / page).read_text()
        if prove and page == "README.md":
            # The control: a status claim naming a version that is not the current one. Without it, a
            # check that finds every claim already correct proves only that it ran.
            text += "\n\nBMX is 0.1 and this sentence is the control.\n"
        for pattern in CLAIMS:
            for m in pattern.finditer(text):
                checked += 1
                if m.group(1) != want:
                    line = text[: m.start()].count("\n") + 1
                    stale.append(f"{page}:{line} claims {m.group(1)}, SPEC.md says {want}: {m.group(0)[:60]}")

    for s in stale:
        print(f"  FAIL  {s}")
    print(f"  {checked} status claims checked across {len(PAGES)} pages")

    if prove:
        if stale:
            print("\nthe control failed as it must — a stale status claim is caught")
            return 0
        print("\nTHE CONTROL DID NOT FAIL, so this check cannot see a stale version")
        return 1
    if not checked:
        print("\nno status claim matched at all, which means the patterns have stopped seeing them")
        return 1
    # **This printed the success line unconditionally, above a `return 1`.** So a reader piping the
    # output — or reading the last line, which is what a summary is for — saw *every version agrees*
    # while the verdict was failure. That is the fourth face of a lying measurement (a runner whose
    # summary contradicts its own exit code), inside the check written the same day to catch stale
    # claims. The success sentence is now earned rather than printed.
    if stale:
        print(f"\n{len(stale)} status claim{'' if len(stale) == 1 else 's'} disagree with SPEC.md")
        return 1
    print("\nevery version the documentation states agrees with SPEC.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
