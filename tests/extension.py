"""Every version an editor artefact declares, checked against the format it paints.

    python3 tests/extension.py
    python3 tests/extension.py --prove-it     # the negative control

**Thirty commits changed the package and the version never moved off 0.1.0.** Measured, not suspected:
`git log -- editors/vscode/bmx-0.1.0.vsix` counted thirty, and unzipping the first one against the last
gives two grammars — an 8,931-byte one that knows only `::: card`, and a 13,235-byte one that knows
`:name:` / `:!name:` — both declaring version 0.1.0.

**That is the worst available failure, because the mechanism that should fix it is the mechanism that
hides it.** VS Code decides whether to offer an update by comparing versions. Anyone who installed the
extension before the 0.7 respelling has a highlighter that paints today's documents wrong, and their
editor tells them they are current. Reinstalling changes nothing. There is no symptom except colour.

**And the cause was ergonomic, which is why no amount of care would have fixed it.** The artefact was
called `bmx-<version>.vsix`, so the version appeared in seven places: two READMEs, three doc pages, the
packer's own docstring, and CI. Bumping it broke every install command in the repository. **A version
that is expensive to change is a version that does not change** — so the filename lost its version
(`bmx.vsix`, stable forever) and the version now lives only where a tool reads it.

That fix removes the friction. This file removes the option:

- **The extension's `major.minor` must equal `SPEC.md`'s.** `SPEC.md`'s title is already the one place
  the version is decided — `tests/version.py` checks every prose claim against it. This is the same rule
  reaching the one claim that check cannot see, because it is JSON inside a zip.
- **The patch is free**, so a packaging fix does not need a format release. What is not free is a format
  release that leaves the extension behind, which is the thing that happened.
- **The committed artefact must be the one the packer writes**, byte for byte — which required making the
  pack reproducible first, because it was not. Three entries carried the current time, so the bytes moved
  on every run and a stale commit was undetectable. Nothing detected it: CI repacks and then inspects the
  result, overwriting the evidence one line before looking for it. **A check that regenerates the artefact
  it is verifying cannot see a stale one.**
- **And the reproducibility is asserted as a property, not by packing twice.** The first version of that
  check packed twice in a row and PASSED on the non-reproducible packer, because a zip stores timestamps
  at two-second granularity and back-to-back runs share a bucket. A three-second sleep exposed it. **A
  test that can only fail when it happens to straddle a boundary is a test that reports success** — see
  [[measurement-instruments-that-cannot-fail]]. One fixed stamp per entry cannot pass by accident.
- **Every filename the documentation tells someone to install must exist.** This is the check that
  matters for the fix itself: the whole point of a stable name is that six documents keep pointing at a
  real file, and the way to lose that is to rename it again.
- **The language server too**, found by grepping for the version I had just removed: it answered
  `initialize` with `0.1.0` while producing 0.12 diagnostics, and its own test asserted the *name* — the
  half that never changes. Read from source rather than over the wire, which is the weaker of the two and
  enough for the failure that actually happens: nobody bumps it.
"""

import json
import pathlib
import re
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PKG = ROOT / "editors" / "vscode" / "package.json"
VSIX = ROOT / "editors" / "vscode" / "bmx.vsix"

# Where somebody is told to install it. A promise to install a file is a promise the file is there.
PAGES = ["docs/editor.md", "docs/install.md", "editors/README.md", "editors/vscode/README.md",
         "editors/vscode/pack.py", "tools/check.sh", ".github/workflows/ci.yml"]


def spec_version():
    """The one place the format's version is decided: the normative document's title."""
    first = (ROOT / "SPEC.md").read_text().split("\n", 1)[0]
    m = re.search(r"BMX (\d+\.\d+)", first)
    if not m:
        sys.exit("SPEC.md's first line does not name a version, so nothing can be checked against it")
    return m.group(1)


def main():
    prove = "--prove-it" in sys.argv
    failures = 0

    def check(ok, ok_line, fail_line):
        nonlocal failures
        if ok:
            print(f"  ok    {ok_line}")
        else:
            failures += 1
            print(f"  FAIL  {fail_line}")

    want = spec_version()
    declared = json.loads(PKG.read_text())["version"]
    if prove:
        # The control is the defect exactly as it happened: a format release ships, the extension is not
        # bumped, and the packaged grammar is newer than the version that describes it.
        declared = "0.1.0"

    check(declared.startswith(want + "."),
          f"the extension declares {declared}, which is SPEC.md's {want}",
          f"the extension declares {declared} and SPEC.md says the format is {want} — "
          f"an editor comparing versions will not offer this to anyone holding an older {declared}")

    # The version a tool actually reads is the one in the manifest, built by `pack.py` from
    # `package.json`. Two files, so they can disagree.
    with zipfile.ZipFile(VSIX) as z:
        manifest = z.read("extension.vsixmanifest").decode()
        packed = json.loads(z.read("extension/package.json"))["version"]
    m = re.search(r'<Identity[^>]*Version="([^"]+)"', manifest)
    check(m and m.group(1) == packed == json.loads(PKG.read_text())["version"],
          f"the manifest, the packaged manifest and the source agree on {packed}",
          f"the manifest says {m.group(1) if m else '(none)'}, the packaged package.json says {packed}, "
          f"and the source says {json.loads(PKG.read_text())['version']}")

    # **Reproducibility first, because it is what makes the next check mean anything.**
    #
    # Asserted as a property of the archive rather than by packing twice and comparing. The version of
    # this that packed twice in a row PASSED on a packer that stamped the current time in three entries —
    # a zip stores timestamps at two-second granularity, so back-to-back runs land in the same bucket. It
    # took a three-second sleep to expose it. **A test that can only fail when it happens to straddle a
    # boundary is a test that reports success.** One fixed stamp for every entry cannot pass by accident.
    with zipfile.ZipFile(VSIX) as z:
        stamps = {i.date_time for i in z.infolist()}
    if prove:
        stamps = stamps | {(2026, 8, 18, 19, 48, 36)}
    check(len(stamps) == 1,
          f"every entry carries one fixed timestamp {sorted(stamps)[0]}, so two packs give one artefact",
          f"entries carry {len(stamps)} different timestamps, so the bytes move on every run and a "
          f"stale commit cannot be detected: {sorted(stamps)}")

    # **And the committed artefact is the one the packer writes.** Compared against a repack, which is
    # what nothing did before: CI packs and then inspects the result, so it overwrites the evidence one
    # line before looking for it. **A check that regenerates the artefact it verifies cannot see a stale
    # one.** The packed bytes are restored afterwards either way, so this never leaves a dirty tree.
    before = VSIX.read_bytes()
    subprocess.run([sys.executable, str(ROOT / "editors" / "vscode" / "pack.py")],
                   capture_output=True, check=True, cwd=ROOT)
    after = VSIX.read_bytes()
    VSIX.write_bytes(before)
    if prove:
        after = before + b"stale"
    check(before == after,
          f"the committed .vsix is what the packer writes ({len(before)} bytes)",
          "the committed .vsix is not what the packer writes — it was changed without repacking")

    # **The language server had the same defect, found by grepping for the version I had just removed.**
    # It answered `initialize` with `serverInfo: {name: 'bmx-lsp', version: '0.1.0'}` while reporting 0.12
    # diagnostics, and `editors/lsp/test/protocol.mjs` checked the NAME — the half that never changes —
    # and not the version. A client puts `serverInfo` in its log, so a stale one misdirects the first
    # question anybody asks about a diagnostic: which version produced it.
    lsp = (ROOT / "editors" / "lsp" / "bmx-lsp.mjs").read_text()
    m = re.search(r"serverInfo:\s*\{[^}]*version:\s*'([^']+)'", lsp)
    served = "0.1.0" if prove else (m.group(1) if m else None)
    check(served is not None and served.startswith(want + "."),
          f"the language server answers `initialize` with {served}",
          f"the language server reports version {served} while producing {want} diagnostics — "
          f"a client logs that, so every bug report about it names the wrong version")

    # And the name every document hands to a reader.
    named = set()
    for page in PAGES:
        named.update(re.findall(r"\b([\w.-]+\.vsix)\b", (ROOT / page).read_text()))
    if prove:
        named.add("bmx-0.1.0.vsix")
    missing = sorted(n for n in named if not (ROOT / "editors" / "vscode" / n).exists())
    check(not missing,
          f"every .vsix the documentation names exists ({', '.join(sorted(named))})",
          f"the documentation tells someone to install {', '.join(missing)}, which is not in the tree")

    # A leftover from the old scheme is a second answer to "which one do I install".
    stale = sorted(p.name for p in (ROOT / "editors" / "vscode").glob("bmx-*.vsix"))
    check(not stale, "no versioned .vsix is left over from the old naming",
          f"{', '.join(stale)} is still in the tree beside bmx.vsix")

    print()
    if prove:
        if failures:
            print("the control failed as it must — an unbumped version, a stale artefact and a "
                  "documented filename that does not exist are all caught")
            return 0
        print("THE CONTROL DID NOT FAIL, so this check cannot see the defect it exists for")
        return 1
    if failures:
        print(f"{failures} thing{'' if failures == 1 else 's'} wrong with the packaged extension")
        return 1
    print(f"every editor artefact declares {declared}, packed from source, named the same thing everywhere")
    return 0


if __name__ == "__main__":
    sys.exit(main())
