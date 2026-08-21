# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

BMX is a **markup format**, not an application: a normative grammar plus a conformance suite, with
two implementations of it living alongside. There is no build step and no package manifest at the
root — the toolchain is `python3` (tests and tools) and `node` (the reference parser and the editor
tests). The Burxt half additionally needs a released `burxt` on `PATH` and `BURXT_LIB` set.

Nothing here is compiled or installed to be worked on. Editing a `.md` normative document, a test
case, or `reference/bmx.js` is the whole loop.

## Commands

```sh
# Everything CI runs, in one command. Start here.
tools/check.sh
BURXT_LIB=<burxt>/lib PATH=<burxt>:$PATH tools/check.sh    # includes the Burxt half

# The conformance suite against any implementation
python3 tests/harness.py 'node reference/bmx.js'

# One case, by hand — the harness has no filter flag
node reference/bmx.js tests/cases/024-block-simple.bmx        # prints the AST as JSON
diff <(node reference/bmx.js tests/cases/024-block-simple.bmx) tests/cases/024-block-simple.json
node reference/bmx.js --render tools/ex1.bmx                   # level-1 HTML

# Two implementations must agree, on ASTs and on pages
burxt build burxt/examples/parse.bx -o /tmp/bmx-parse
python3 tests/agree.py 'node reference/bmx.js' /tmp/bmx-parse
burxt build tools/render.bx -o /tmp/bmxrender
python3 tests/renders.py /tmp/bmxrender
python3 tests/output.py 'node reference/bmx.js --render' /tmp/bmxrender

# Level 2 (Burxt only): a document becomes a view the compiler checks
burxt run burxt/guarantees.bx

# Documentation gates
burxt build tools/fmt.bx -o /tmp/fmt
/tmp/fmt --check docs/*.md docs/guide/*.md README.md editors/vscode/README.md
/tmp/fmt docs/*.md                      # rewrite in place

# Editor surface
cd editors/vscode && npm install vscode-textmate vscode-oniguruma   # what scopes.mjs needs
node editors/vscode/test/scopes.mjs
node editors/lsp/test/protocol.mjs
python3 editors/vscode/pack.py          # writes editors/vscode/bmx.vsix, which is committed
```

`tools/check.sh` **mirrors `.github/workflows/ci.yml` and nothing else**. When a check is added to
one, add it to the other in the same commit; the two drifting is the failure this file exists to
prevent.

## The test suite is the specification

`tests/cases/NNN-name.bmx` + `.json` is *input → expected AST*. `tests/errors/NNN-name.bmx` +
`.error` is *input → expected error code* (the `.error` file holds only the `BMX-Ennn` code; the
message is each implementation's own words and is not compared). The cases are **data**, so
conformance in a new language costs an afternoon rather than a port — `tests/harness.py` is
thirty lines and is deliberately *not* part of the specification.

Where `SPEC.md` and `tests/` disagree, **the tests win**. A claim in prose that no runner checks is
a claim no implementation has to honour, and this repository's history is largely the story of
converting such claims into checks.

Beyond conformance, `tests/` holds meta-checks over the repository itself — `version.py`,
`messages.py`, `portability.bx`, `branding.py`, `extension.py`, `surface.py`,
`output.py`, `invitation.py`. Most take **`--prove-it`, a negative control** that asserts the check can fail; CI runs
both halves, because a check nobody has watched fail is a check nobody has tested. Add the control
when you add a check.

`tests/probe.py` (`speaks(command, "ast"|"page")`) is why runners diagnose a wrong binary instead of
blaming every document — call it from any new runner that takes a command.

## Versioning rules that bite

- **The version lives in exactly one place: the title of `SPEC.md`.** `tests/version.py` greps every
  status claim in the docs, `docs/_config.yml`'s `bmx_version`, and the site layout against it. If
  you invent a new phrasing for "BMX is version X", add its shape to that script or it goes
  unchecked. Its scope is now **every `.md` in the tree**, not a list — it was a literal list of six
  files, and `docs/index.md` sat outside it claiming 0.4 for eight minors. A file that is mostly
  version *history* opts out with a `<!-- version-claims: historical -->` marker **in itself**
  (only `VERSIONING.md` does), so the exception lives in the file it describes rather than
  accumulating in the checker. **When you add a check here, ask what its own scope is
  hand-maintained on**; that is where the next stale claim will sit.
- **An edited case in `tests/cases/` proves a major. Nothing proves a minor.** The second half is the
  part to be careful with — added cases cannot acquit, a *deleted* refusal in `tests/errors/` is a
  widening (minor), and a defect found inside its own release has no window for anyone to depend on
  it. `VERSIONING.md` works each exception through the release that found it. Always ask by hand:
  *what document is valid today whose meaning this changes?*
- **Error codes are permanent.** Never reused, never renumbered; retiring a rule retires its code.
- **A git tag's prefix says which implementation; its digits say which format** (`burxt-0.12.2`),
  never a bare `v0.x`. `VERSIONING.md` said the opposite until 2026-08-20 — measured: `burxt-0.12.2`
  tags a release in which `burxt/bmx.bx` is byte-identical. The distinction it draws (adding an AST
  variant is a minor for the format, a major for any package exposing the AST) still binds anyone
  packaging BMX elsewhere; this repository declined to pay for a second number.
- **`burxt.package` declares `version 0.12.2`, which is the format's**, and says so in a comment so
  no reader takes it for an API promise. (No tool reads it: `burxt review --semver` takes two source
  paths and a `--require` operand — verified, after I asserted the opposite from the command's name.)
  `tests/version.py` checks it by path — not as a prose pattern, since `docs/install.md` shows a
  *consumer's* manifest whose `version 0.1.0` a generic pattern would flag.
- **The VS Code extension's version must equal the format's** (`tests/extension.py`), and the
  committed `bmx.vsix` must be the packed one. The version is not in the filename, on purpose.
- CI pins the Burxt it supports (`BURXT` env in `ci.yml`) to a **released** tarball, never a branch.
  Raise it deliberately, in its own commit.

## Architecture

**The normative documents** are the actual artifact, and each owns a distinct question:

| | |
|---|---|
| `SPEC.md` | the grammar, the AST shape, the error codes, and §7's deliberate absences with the trigger that would earn each one |
| `BOUNDARY.md` | what BMX owns vs. the host; conformance level 1 (renders) and level 2 (checks slot expressions before render) |
| `ESCAPING.md` | output escaping — the one place BMX is opinionated about output |
| `VERSIONING.md` | the suite-as-semver rule and every release that tested it |

**Two implementations, and the split in their directory names is deliberate: `reference/` is a role,
`burxt/` is an audience.**

- `reference/bmx.js` — zero dependencies, written to be read (no lookup tables, no regex where a
  loop is clearer), because somebody porting BMX to a third language reads it top to bottom. Exports
  `parse`, `render`, `lint`, `at`, `BmxError`; also a CLI (`[--render] <file>`). Its Node floor is
  **14**, measured, and `tests/portability.bx` reads that floor out of `docs/install.md` so the
  number lives in one place.
- `burxt/bmx.bx` — the Burxt implementation, for Burxt programs. Level 1 today; level 2 (a document
  becomes a `pure function … -> Html` whose slots the compiler type-checks) is its road, exercised by
  `burxt/guarantees.bx`. Its `public` surface is a compatibility promise checked in **both** directions by
  `tests/surface.py`: every documented name must be reachable from an outside package, and every
  public name must be documented.

The two must agree — `agree.py` (ASTs, including on documents no case covers, which is where a
spec's ambiguities live), `renders.py` (pages), `output.py` (that neither renderer lets a document
reach output through a link target or an info string). Both implementations currently have one
author, so agreement catches drift and regression rather than proving the spec unambiguous; 1.0
requires a third-party implementation.

**Two invariants in the parsers that explain a lot of the code:**

- Leading spaces are removed **once**, in the line/row builder, so every offset downstream is
  already a real source position. Code blocks keep everything but their fence's indentation.
- Every node except `text` and `code_span` carries an `offset` that is the byte index of the **first
  byte the author wrote** for that construct. A block's `offset` is its fence and its `head_offset`
  is its head. A slot's `offset` is the first byte of the *trimmed* expression. Adjacent `text` nodes
  are always merged.

**`editors/`** ships highlighting and the format's half of a language server — `bmx-lsp.bx`, a Burxt
binary since 2026-08-21, which removed `node` from what any editor needs to get diagnostics and added a
build step for anyone without a Burxt toolchain. Its test moved to CI's Burxt job for the same reason. It colours structure
only and leaves three scopes deliberately uncoloured — `meta.slot.expression.bmx`,
`meta.block.head.bmx`, `meta.inline-block.head.bmx` — which are **a compatibility surface, not an
implementation detail**: hosts inject their expression language into them, so renaming one is a major
change, and `test/scopes.mjs` asserts them by name. Hosts extend by injection; nothing in this
repository should need patching for a host. `editors/vscode/reference/` is staged from
`reference/bmx.js` by `pack.py` and is gitignored — two copies of a parser in version control is how
they drift.

**`docs/`** is a Jekyll site served at bmx.burxt-lang.org. Two things bite:

- A page documenting `{{ … }}` is a page Jekyll reads as Liquid, so **every doc page wraps its body
  in `{% raw %}`/`{% endraw %}`**, and an unclosed one takes the whole site build down. CI counts
  them, because there is no Ruby locally — a green local run says nothing about whether the site
  builds.
- **Examples must be indented by `tools/fmt.bx`.** Indentation is insignificant to the parser, so a
  wrongly-indented example parses perfectly and teaches a reader the wrong shape; nothing but this
  gate can see it. `site.css`/`site.js` are byte copies from burxt-lang.org — re-copy, don't edit.

**`tools/`** generates every rendered panel on the site from real renderer output — `page.bx`,
`errpage.bx` and `showcase.bx` (all Burxt, ported from Python and verified byte-identical against the
committed artefacts), `shot.mjs` (PNGs via the local puppeteer). Screenshots are the one artifact no test can catch going stale, so **regenerate them
whenever renderer output changes**; `tools/README.md` is the record of that pipeline and of what the
format's real limits are (BMX has no attribute syntax — that, not navigation bars, is the wall).

## Why so little of this repository is Burxt

**The rule across all three projects: if it can be written in Burxt, it must be, and reaching for
another language is a gap report rather than a solution.** BMX is the furthest of the three from it by
raw count — measure with `python3 tests/languages.py` — and it has the strongest defence, which is why
every non-Burxt file **states its reason in its own first 20 lines** (`not-burxt: <reason>`) and the
check fails on a file that states none. A count without reasons reads worse than the truth: on 2026-08-20
an outside audit read 8,125 lines by counting the gitignored copy of `reference/bmx.js` that `pack.py`
stages — the same file twice. **Run `python3 tests/languages.py` for today's numbers rather than reading
one here**; this file has been wrong about them once, and the gitignored rules file beside it twice.

Three of the reasons are properties of BMX being a *format*, and they are not negotiable:

- `reference` — `reference/bmx.js` is JavaScript **on purpose**. The format's central claim is that any
  language can implement it; a reference in the host language makes that claim untestable by anyone who
  does not have the host.
- `neutral` — `harness.py`, `probe.py`, `agree.py`, `renders.py`, `output.py` take an **arbitrary
  implementation command**. In Burxt, a stranger implementing BMX in a sixth language could not run
  them, which is the only thing they exist for.
- `bootstrap` — `tools/check.sh` alone: the entry point a contributor runs **before** a toolchain
  exists, so it cannot need what it installs.

**A category was deleted on 2026-08-21 because it was doing work it had not earned.** `standalone`
covered sixteen files on the strength of `ci.yml`'s sentence — *the format must be testable without its
first host installed* — and **that sentence is about the format, not about this repository's CI.** The
format's claim needs the fixtures, which are data, plus a runner a stranger can run: that is `neutral`.
`tests/version.py`, `tests/branding.py`, `editors/vscode/pack.py` and twelve others check *this
repository*. In Burxt they cost a contributor without a toolchain some local checks and cost the
portability claim nothing. Fifteen files moved to `gap`; **the gap went from 708 lines to 3,086.** The
number had been wrong in the flattering direction.

`platform` is forced by the runtime (VS Code's extension host is Node; a TextMate grammar is tokenised
by a JS engine; `docs/assets/code.js` runs in a reader's browser) and `vendored` is a byte copy from
burxt-lang.org that must not be edited at all.

**Two questions sort every entry here, and the second is the one that gets skipped.** *Which job runs
this, and is that job allowed to need Burxt* — and then *is the capability actually absent, or did I stop
checking*. The first forbids things a release cannot unforbid: `editors/vscode/pack.py` and
`tests/branding.py` are reachable from the conformance job, so a zip module or a PNG decoder in Burxt
changes nothing about them. The second is how `docs/assets/code.js` sat in `platform` claiming a browser
needs JavaScript, months after Burxt reached a browser through wasm. The Burxt session, who sharpened this
from the question into its two halves, found their own instance the same day.

**`gap` is the only category that should ever shrink**, and it is named rather than defended:
`tests/surface.py` **already requires the Burxt toolchain**, so it has no standalone defence and is
the real remaining gap — as did `burxt/test.py`, now `burxt/guarantees.bx`, and `editors/lsp/bmx-lsp.mjs`, now `bmx-lsp.bx`; `docs/assets/code.js` could be Burxt through wasm but would cost the
documented promise that Helix and Neovim need *only Node*; `tools/shot.mjs` is blocked on Burxt having
no browser driver. The check prints the gap and caps nothing — a threshold is a number somebody raises
when it is inconvenient.

**`burxt/conformance.bx` is that move, and it exists now.** A Burxt program driving `burxt/bmx.bx`
over `tests/cases` and `tests/errors` — 92/92 — so the implementation shipped for Burxt users is
verified by the language it serves, while `harness.py` stays exactly what it is: the neutral runner for
everyone else. Two runners, one question, opposite sides; if they disagree, one has a bug and the
fixtures decide. Run it with `burxt run burxt/conformance.bx` from the root, or build it to `-o` and
pass a suite directory — **`burxt run` cannot pass a program an argument**, since `burxt build <file>
[link args…]` reads anything after the file as a link argument. That is how `burxt/examples/parse.bx`
turned out to have documented an invocation that never worked.

**`burxt/guarantees.bx` is the level-2 half, ported from `burxt/test.py`** — the same thirteen
assertions under the same names, verified by running both and diffing before the Python was retired. It
needed one capability the fixture runner did not: `os_capture_status`, which keeps stdout and stderr
apart, so a refusal asserted to *start with* `BMX-G001` cannot be prefixed by whatever the generator
printed first. `burxt run burxt/guarantees.bx`.

The remaining gap of that shape is **`tests/surface.py`** — the ledger prints its size, deliberately not
repeated here — which needs a third capability again: it writes a dependent package into a temp directory and builds it, to prove every documented
name is reachable from *outside* this package. `docs/assets/code.js` is a decision rather than a task
— it would cost the documented promise that Helix and Neovim need *only Node*.

## The sibling repositories, and the one mistake to expect

The toolchain is installed at `~/.local/bin/burxt` with `~/.local/lib/burxt/` — so the Burxt half of
`tools/check.sh` runs locally, 30 checks rather than 20, and `BURXT_LIB` is not needed for `burxt run`.
Set it for `check.sh`, whose guard tests the library rather than the binary.

**Measure it; do not trust its version string, and do not trust this paragraph either.** For most of
2026-08-20 the installed compiler reported `burxt 1.4.0` while being a different binary from the published
1.4.0 — which is how star-burxt lost a branch: they moved their packer to `std/zip.bx`, it built locally,
and `main` went red on a clean runner because the published 1.4.0 ships no zip module. **By the end of that
day it had been replaced and is byte-identical to the published 1.5.0** (`1d920478…` both). So the hazard
is not currently live on this machine, and **that is exactly why the instruction is to measure rather than
to remember**: a warning about a condition that has lifted reads as one that has not, and the next
replacement is invisible until someone hashes it.

    md5sum "$(command -v burxt)"        # against the published asset's, below

So **verify Burxt work against the release, not against what is installed** — and *the release* means
the published asset, checksum-verified, **not `~/burxt/dist/`**:

```sh
v=1.5.0
gh release download "v$v" --repo andrecorugda/burxt --dir /tmp/rel \
    --pattern "burxt-$v-linux-x86_64.tar.gz" --pattern SHA256SUMS --clobber
(cd /tmp/rel && sha256sum -c --ignore-missing SHA256SUMS)      # the step that makes it the release
tar xzf /tmp/rel/burxt-$v-linux-x86_64.tar.gz -C /tmp/rel --strip-components=1
PATH=/tmp/rel:$PATH BURXT_LIB=/tmp/rel/lib tools/check.sh
```

**`~/burxt/dist/` holds LOCAL BUILDS and this file recommended it.** Measured — the same tag, three
different byte streams:

| | 1.4.0 | 1.5.0 |
|---|---|---|
| `~/.local/bin/burxt` (installed) | — | reports `1.4.0`, differs from every tarball |
| `~/burxt/dist/…tar.gz` | `6670264f…` | `58429358…` |
| the published release asset | `161e6ecb…` | `44d3b566…` |

Three layers of the same error, each one believed to be the ground: the installed compiler, then the
`dist/` tarball, then the published asset. **Only the third is what CI downloads**, and only a checksum
tells them apart — `burxt --version` prints the same string for all of them.

**Raising the pin has a second job: re-test the dated claims.** Grep for `Dated` before bumping `BURXT`.
**All three that stood on 2026-08-21 resolved with the 1.7.0 pin raise, and the pattern held: each was
cheap to act on and would have been invisible without something watching.** `reference/bmx.js`'s escape
table moved in the same commit as the pin, caught by `tests/cases/081`. The hand-written tables in
`tools/page.bx` and `tools/errpage.bx` are gone, because `html_escape` now matches Python byte-for-byte —
verified by the panel check rather than by reading. And `burxt run … -- args` works from 1.6.0 while the
documented form stays build-then-run, because `docs/install.md`'s floor is 1.3.0: **a capability arriving
is not permission to document it.**
The habit has already paid once: both `.bx` files stated that `burxt run` cannot pass a program an
argument, which was true of published 1.5.0 and is false from 1.6.0 — verified against the downloaded
asset rather than on its author's word, after an earlier report of the same fix turned out to exist only
in their tree.

**And the resolution did not change the documented command, which is the part worth copying.** The floor
in `docs/install.md` is 1.3.0, and `run --` fails on everything before 1.6.0 — so a usage line has to work
for the version a reader is told is enough, not for the newest one. A capability arriving is not
permission to document it.

`git grep -l "function <name>(" v1.5.0 -- lib` in `~/burxt` answers the narrower question — whether a
symbol exists in the release — without a build, **and that shortcut is sound for a measured reason rather
than an assumed one: all 29 `lib/*.bx` in the published 1.5.0 asset are byte-identical to `v1.5.0:lib/`.**
The library *is* the tag; the binary is compiled and need not be, which is the whole distinction and why
the digest check above cannot be replaced by this one. `print_error`, `substring`, `push` and `len` are
compiler builtins and will not be found in `lib` at all.

`~/burxt` (the language) and `~/star-burxt` (the framework above BMX) are **readable from here**, and
BMX's docs make claims about both — what `burxt review --semver` reads, how a `dependency` line
resolves, what star injects into a scope.

**Verify those in their tree; do not infer them from a name.** This session asserted, in four files,
that `burxt review --semver` reads `burxt.package` — reasoning from the command's name, which sounds
like it reads a declared version. It does not: `review.rs` has no reference to any manifest, and the
claim under test arrives as a `--require` operand. Its author corrected it.

The tempting excuse is that a cross-repository claim is expensive to check. **It was one `grep`** —
run in seconds once corrected. The default silently flipped from *verify* to *assume* not because
checking was costly but because it never registered as available, and every other claim that hour was
about a file in this tree. Three repositories describing each other will produce this again in both
directions, and it already has.

## Conventions in this codebase

- **Comments carry the defect that caused the code.** `ci.yml`, `check.sh`, and the test runners
  explain what went wrong, in which release, and why the check is shaped the way it is. Match that:
  a check added without its motivating failure is one somebody deletes as noise.
- **Commit subjects are a sentence stating the finding**, not an imperative summary — e.g. *"The
  formatting claim finally has a test, and bmx.bx was not formatted"*.
- Prefer converting a prose claim into a runner over restating it. Prefer one helper with five
  callers over five copies of a smoke test.
