# not-burxt: gap — checks THIS REPOSITORY rather than the format, so the standalone argument never reached it
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
  the version is decided — `tests/version.bx` checks every prose claim against it. This is the same rule
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
  test that can only fail when it happens to straddle a boundary is a test that reports success.** One
  fixed stamp per entry cannot pass by accident.
- **Every filename the documentation tells someone to install must exist.** This is the check that
  matters for the fix itself: the whole point of a stable name is that six documents keep pointing at a
  real file, and the way to lose that is to rename it again.
- **The language server too**, found by grepping for the version I had just removed: it answered
  `initialize` with `0.1.0` while producing 0.12 diagnostics, and its own test asserted the *name* — the
  half that never changes. Read from source rather than over the wire, which is the weaker of the two and
  enough for the failure that actually happens: nobody bumps it.
- **And the install PATH, which is the same promise one step out.** A page naming a `.vsix` that is not in
  the tree is checked above; a page naming an extensions *directory* that does not exist on the reader's
  machine is the same defect and was not. `~/.vscode/extensions` is wrong in every remote window — VS Code
  Server loads extensions from the remote host — and **the machine BMX is developed on has no such
  directory.** The star-burxt session lost Andre a day to exactly this sentence in star's docs: three
  finished grammars, packed correctly, never installed, no error to search for because a `cp` into a path
  whose parent exists succeeds silently. `code --install-extension` is the instruction that removes the
  class, because it resolves the directory and prints which machine it used.

  So: every page that tells somebody to install must name `code --install-extension`, and a page naming a
  raw extensions directory must name the remote one beside it. **This is a lint on prose, which is the only
  kind of check available** — CI has no VS Code, so the instruction cannot be executed, only kept honest.
"""

import io
import json
import pathlib
import re
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PKG = ROOT / "editors" / "vscode" / "package.json"
VSIX = ROOT / "editors" / "vscode" / "bmx.vsix"
PACK = ROOT / "editors" / "vscode" / "pack.py"

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

    # **And the archive is a well-formed extension, asserted HERE rather than by a second step that
    # packs.** `tools/check.sh` used to run `pack.py` again to inspect the result, three lines after the
    # comparison above — so a stale artefact was detected and then silently repaired inside one
    # invocation, and the second local run was always green. Guarding that with a park-and-restore worked
    # and was the wrong fix: **the collision is eliminated by having exactly one thing pack.** star-burxt
    # reached the same place from the other side and their CI says so in one line — *runs the test, not
    # the packer* — which is why a planted stale artefact survives two runs in their tree.
    #
    # Read from the bytes rather than the file, so nothing on disk is touched at all. The entry list is
    # written out rather than globbed, because a missing entry is only ever found by packaging.
    need = ["[Content_Types].xml", "extension.vsixmanifest", "extension/package.json",
            "extension/syntaxes/bmx.tmLanguage.json", "extension/icon.png"]
    if prove:
        need = need + ["extension/a-file-the-packer-never-writes"]
    packed = zipfile.ZipFile(io.BytesIO(after))
    missing_entries = [n for n in need if n not in packed.namelist()]
    check(not missing_entries,
          f"the packed archive carries all {len(need)} entries an editor needs, and is not corrupt",
          f"the packed archive is missing {missing_entries}")
    check(packed.testzip() is None, "the archive is readable end to end",
          "the archive is corrupt")

    # **The language server had the same defect, found by grepping for the version I had just removed.**
    # It answered `initialize` with `serverInfo: {name: 'bmx-lsp', version: '0.1.0'}` while reporting 0.12
    # diagnostics, and `editors/lsp/test/protocol.mjs` checked the NAME — the half that never changes —
    # and not the version. A client puts `serverInfo` in its log, so a stale one misdirects the first
    # question anybody asks about a diagnostic: which version produced it.
    # **The file and the pattern both moved when the server was ported to Burxt**, and this check is how
    # I found out: it read `bmx-lsp.mjs`, which no longer exists, and the suite failed on a path rather
    # than on a version. A check keyed to a filename is a check that breaks when the file is right to
    # rename — which is the cheap kind of breakage, because it says so immediately.
    lsp = (ROOT / "editors" / "lsp" / "bmx-lsp.bx").read_text()
    m = re.search(r'json_field\("version",\s*json_text\("([^"]+)"\)\)', lsp)
    served = "0.1.0" if prove else (m.group(1) if m else None)
    check(served is not None and served.startswith(want + "."),
          f"the language server answers `initialize` with {served}",
          f"the language server reports version {served} while producing {want} diagnostics — "
          f"a client logs that, so every bug report about it names the wrong version")

    # And the name every document hands to a reader.
    #
    # **Only names on an `install-extension` line, because the promise IS the install command.** This
    # scanned every `.vsix` token on every page, which cannot tell **using** a name from **mentioning**
    # one — so a sentence recording the old scheme (*"the artefact used to be called `bmx-0.1.0.vsix`"*)
    # failed the check for describing history accurately. Proven reachable by appending exactly that
    # sentence to `editors/vscode/README.md` and watching this fire; latent only because no page happens
    # to carry it today. The Burxt session hit the identical bug in their own filename test twice and had
    # to reword prose to get green, which is the wrong direction — a check should not constrain what the
    # documentation may say about its own past.
    #
    # The same use-versus-mention failure took a file out of `tests/version.bx`'s scope the same day, when
    # `CLAUDE.md` opted itself out by *describing* the opt-out marker. Both fixes are structural: there,
    # a declaration must stand alone at the top of a file; here, a promise must stand in a command.
    #
    # Internal paths — the `ZipFile(...)` lines in `check.sh` and `ci.yml` — are deliberately not scanned.
    # They are not promises to a reader, and they are self-checking: opening a missing zip throws.
    # **A SPLIT, not a character class, and that distinction is the day's best transferable finding.**
    # This was `re.findall(r"\b([\w.-]+\.vsix)\b", line)`, and `code --install-extension
    # bmx-<version>.vsix` matched NOTHING: the character before `.vsix` is `>`, which the class does not
    # admit, so the scan could not reach the name and a wrong filename on a real install line passed
    # silently. Verified before changing it.
    #
    # **A character class enumerates what a filename may contain; splitting on delimiters accepts whatever
    # is actually there.** Prose contains things filenames do not — placeholders, ellipses, a name inside
    # parentheses — and each of those is a hole in a class and none is a hole in a split. The Burxt
    # session's equivalent check catches the placeholder for exactly this reason, which they were candid
    # was an accident of their predicate rather than foresight; it is still the right shape, and it is why
    # their check found this class of defect in anger while mine could not see it.
    #
    # **And the lesson's second half, which is symmetric and cost two measurements to find:**
    #
    #     A class misses what it did not enumerate. A split accepts what it should not.
    #
    # The class missed `bmx-<version>.vsix` because `>` was not in it. The split then failed at the other
    # end of the same token: pointed at `editors/README.md` — the page about how a HOST extends BMX — a
    # legitimate `code --install-extension star-burxt.vsix` was reported as a missing file of ours.
    # Measured, not imagined; that page is the likeliest place such a line gets written.
    #
    # So the split is filtered to OUR artefact, by the name `package.json` declares rather than a literal,
    # which is the guard the Burxt session's predicate had all along (`ends_with(".vsix") && contains
    # ("burxt")`) and that I dropped in switching to theirs. Their check lost to punctuation at the same
    # time mine lost to a placeholder — neither predicate was better, they failed at opposite ends of one
    # token, and **both wanted the trim**, which is the cheap half neither of us had before today.
    #
    # Trailing punctuation is trimmed so a sentence-ending `bmx.vsix.` and a parenthesised
    # `(bmx-0.1.0.vsix)` are still the names they name — both walked past their check untrimmed, in the
    # file where such a sentence is most plausible. A path is reduced to its basename because
    # `editors/vscode/bmx.vsix` promises the same file.
    ours = json.loads(PKG.read_text())["name"]

    def promised(text):
        out = set()
        for line in text.splitlines():
            if "install-extension" not in line:
                continue
            for token in re.split(r"[\s`'\"(),]+", line):
                token = token.strip("`'\".,;:!?()")
                if token.endswith(".vsix") and ours in token:
                    out.add(token.rsplit("/", 1)[-1])
        return out

    named = set()
    for page in PAGES:
        named.update(promised((ROOT / page).read_text()))
    if prove:
        # Through `promised`, not straight into the set: a control that skips the extractor proves the
        # comparison works and says nothing about whether the extractor still sees an install line.
        named.update(promised("code --install-extension bmx-0.1.0.vsix"))
    missing = sorted(n for n in named if not (ROOT / "editors" / "vscode" / n).exists())
    check(not missing,
          f"every .vsix the documentation names exists ({', '.join(sorted(named))})",
          f"the documentation tells someone to install {', '.join(missing)}, which is not in the tree")

    # The path half of the same promise. A directory is not a file, so the check above cannot see it.
    LOCAL, REMOTE = "~/.vscode/extensions", "~/.vscode-server/extensions"
    bare, teaches = [], []
    for page in PAGES:
        body = (ROOT / page).read_text()
        if prove and page == "editors/README.md":
            # The control is the defect as it was written: the local directory, alone, in an instruction.
            body = body.replace(REMOTE, "~/.vscode/extensions-CONTROL")
        if "install-extension" in body:
            teaches.append(page)
        # A page may mention the local directory freely — it must not be the ONLY one it names, because a
        # reader in a remote window follows it into a directory nothing reads.
        if LOCAL in body and REMOTE not in body:
            bare.append(page)
    check(not bare,
          f"no page sends a reader to {LOCAL} without naming {REMOTE} beside it",
          f"{', '.join(bare)} names {LOCAL} alone, which is a directory nothing reads in a remote window")
    check(teaches,
          f"the install instruction every page leads with is `code --install-extension` "
          f"({len(teaches)} page{'' if len(teaches) == 1 else 's'})",
          "no page names `code --install-extension`, so every reader is left resolving the "
          "extensions directory themselves")

    # **The packer's own usage line, which promised a filename it stopped writing.** It said
    # `writes bmx-<version>.vsix here` while the code twelve lines from the end writes `bmx.vsix` — stale
    # in the one file whose long comment explains why the version was taken OUT of the filename.
    #
    # **Two checks missed it for the same reason:** `bmx-<version>.vsix` contains `<` and `>`, which are not
    # in `[\w.-]`, so the name-scan above never matched the placeholder at all — not before the
    # install-extension scoping and not after. It was found because the Burxt session objected to that
    # scoping, naming *a docstring claiming output* as a promise site their broader rule covers and mine
    # dropped. They were right that the site matters, and right for a better reason than either of us
    # argued: it was already wrong.
    #
    # So the promise is compared to the behaviour rather than to a pattern — the usage line's filename
    # against the name the packer actually builds. No wording heuristic, and a placeholder cannot slip
    # through, because a placeholder is not equal to a real name.
    writes = re.search(r"writes\s+(\S+\.vsix)\s+here", PACK.read_text())
    builds = f"{json.loads(PKG.read_text())['name']}.vsix"
    promised_out = writes.group(1) if writes else "(no `writes … here` line)"
    if prove:
        promised_out = "bmx-<version>.vsix"
    check(promised_out == builds,
          f"the packer's usage line promises {builds}, which is what it writes",
          f"the packer's usage line promises {promised_out} but it writes {builds}")

    # A leftover from the old scheme is a second answer to "which one do I install".
    stale = sorted(p.name for p in (ROOT / "editors" / "vscode").glob("bmx-*.vsix"))
    check(not stale, "no versioned .vsix is left over from the old naming",
          f"{', '.join(stale)} is still in the tree beside bmx.vsix")

    print()
    if prove:
        if failures:
            print("the control failed as it must — an unbumped version, a stale artefact, a documented "
                  "filename that does not exist, an install path nothing reads and a missing archive "
                  "entry are all caught")
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
