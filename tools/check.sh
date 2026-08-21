#!/usr/bin/env bash
# not-burxt: bootstrap — the entry point a contributor runs BEFORE any toolchain exists; it cannot need what it installs
#
# Everything CI runs, locally, in one command.
#
#     BURXT_LIB=<burxt>/lib PATH=<burxt>:$PATH tools/check.sh
#
# **This exists because I shipped 0.7.0 having run nine of the ten checks, and the tenth was the one
# that failed.** `editors/vscode/test/preview.js` had a `::: card` in it and I never ran it — I had
# assembled the list from memory each time, which works until the one time it does not. A list in a
# shell script cannot skip an entry out of confidence.
#
# It mirrors `.github/workflows/ci.yml` and nothing else. When a check is added there, add it here in
# the same commit; the two drifting is the only way this file becomes worse than no file. `tools/README`
# says the same thing about screenshots and for the same reason.

set -u -o pipefail
cd "$(dirname "$0")/.."

pass=0
fail=0
# **What was NOT run, because the summary line said only what was.** A fresh clone of this repository
# reports `26 checks passed` where a complete tree reports 29 — the three grammar tests need an `npm
# install` that a clone does not have — and a reader comparing that number against CI's has no way to see
# the difference. The skips were printed, four lines apart from a total that ignored them; `tests/version.bx`
# carries the same defect written up as *a runner whose summary contradicts its own exit code*, and this is
# its milder cousin: a summary that is true about what ran and silent about what did not.
#
# **The counts in the skip labels are hand-written and were wrong on the first try** — the Burxt half was
# labelled 8 and is 9, which showed up only because 17 passed + 3 + 9 has to equal the 29 a complete tree
# runs, and 17 + 3 + 8 did not. `grep -c '^  run '` inside each guarded block is the check; if a `run`
# line is added to a block, its number here moves.
#
# **A check that only ever runs where the tree is complete cannot find an incomplete tree** — the
# star-burxt session's sentence, after four red `main` runs traced to files their local tree had and a
# runner did not. This is the reporting half of it.
skipped=0
skipped_what=""
skip() {
  printf '  \033[33mskip\033[0m  %s\n' "$1"
  skipped=$((skipped + 1))
  skipped_what="${skipped_what}${skipped_what:+; }$2"
}
# **The counts in the skip labels were hand-written, and they went stale exactly as the note above said
# they would.** The Burxt half was labelled 9 while its block held 14 `run` lines — five checks a reader
# of a skipped run could not know they were missing, and the label had been bumped by hand twice on the
# way there without anyone counting. The note even names the fix (`grep -c '^  run '` inside the block)
# and then asks a person to do it. So the script counts its own blocks now; a label cannot drift from a
# list it is derived from.
group_size() {
  awk -v tag="# group: $1" '
    index($0, tag) == 1 { on = 1; next }
    on && /^  run / { n++ }
    on && /^else$/ { on = 0 }
    END { print n + 0 }' "${BASH_SOURCE[0]}"
}
run() {
  local name="$1"; shift
  local out
  if out=$("$@" 2>&1); then
    printf '  \033[32mok\033[0m    %s\n' "$name"
    pass=$((pass + 1))
  else
    printf '  \033[31mFAIL\033[0m  %s\n' "$name"
    printf '%s\n' "$out" | tail -12 | sed 's/^/          /'
    fail=$((fail + 1))
  fi
}

echo "the format, and both implementations of it"
# **This line said `tests/cases` and `-ge 20` while CI said both folders and `-ge 39`** — so the file
# whose header promises to mirror `ci.yml` was checking a different set against a different floor, and
# the local run was the weaker of the two. Found while adding the implementer page, which states the
# suite's size in prose and therefore needed to know which number was load-bearing. Both now count both
# folders, and `tests/invitation.bx` owns the floor the documentation claims.
run "the suite is not empty" bash -c '[ "$(ls tests/cases/*.bmx tests/errors/*.bmx | wc -l)" -ge 39 ]'
run "the linter fires where it should and stays quiet where it should" node tests/lints.mjs
run "the parser imports where there is no Node" bash -c '
  node tests/embeds.mjs && node tests/embeds.mjs --prove-it'

echo
echo "the editor surface"
if [ -d editors/vscode/node_modules/vscode-textmate ]; then
# group: editor
  run "the grammar puts every scope where it says it does" node editors/vscode/test/scopes.mjs
  run "the site's colours and the editor's agree" node editors/vscode/test/agrees.mjs
  run "every line is numbered and the document survives painting" bash -c '
    node editors/vscode/test/panel.mjs && node editors/vscode/test/panel.mjs --prove-it'
else
  skip 'the grammar tests need `cd editors/vscode && npm install vscode-textmate vscode-oniguruma`' \
       "the grammar tests ($(group_size editor), no vscode-textmate)"
fi
run "the editor behaves the way the format reads" node editors/vscode/test/config.mjs
# **The staged parser is deleted before it is staged, and that is not belt-and-braces.** `preview.js`
# imports `editors/vscode/reference/bmx.mjs`, which is gitignored, and it **passes against a stale one** —
# measured: staged a copy of the parser from four days earlier and it exited 0. So the `cp` below is the
# only thing making the tested parser the current one, and a leftover satisfies the check just as well.
# There was one: a `bmx.js` in that directory dated four days back, an orphan of an older staging scheme,
# invisible because the directory is ignored.
#
# The Burxt session's rule, after a `.vsix` that `cp -r` had carried into a scratch copy let a packer test
# pass while the packer wrote into the real tree: **delete what you are about to assert the creation of,
# before you assert it.** A single `rm -rf` turns luck into a check.
run "the preview does what the button promises" bash -c '
  rm -rf editors/vscode/reference &&
  mkdir -p editors/vscode/reference &&
  cp reference/bmx.js editors/vscode/reference/bmx.mjs &&
  node editors/vscode/test/preview.js'

echo
echo "the documentation"
run "every doc page closes its raw tag" bash -c '
  bad=0
  for f in docs/*.md docs/guide/*.md; do
    o=$(grep -c "{% raw %}" "$f" || true)
    c=$(grep -c "{% endraw %}" "$f" || true)
    [ "$o" != "$c" ] && { echo "$f: raw=$o endraw=$c"; bad=1; }
  done
  exit $bad'

echo
# **The guard checks the toolchain WORKS, not that a `burxt` exists on PATH.** With `PATH` pointing at a
# directory that had been cleaned out of /tmp, `command -v burxt` happily found the system's 0.0.153 —
# which predates `use "std/…"` — and five checks reported FAIL for a missing standard library. A check
# that cannot tell "this is broken" from "you have not set this up" sends you to debug the wrong thing.
if [ -n "${BURXT_LIB:-}" ] && [ -r "${BURXT_LIB}/option.bx" ] && burxt build /dev/null -o /dev/null 2>&1 | grep -qv 'standard library'; then
# group: burxt
  echo "the Burxt implementation — needs a released burxt on PATH and BURXT_LIB set"
  run "it compiles" bash -c 'burxt build burxt/examples/parse.bx -o /tmp/check-parse'
  # Needs burxt 1.4.0 or newer, which is the pinned version — `fmt` did not exist before it.
  # **Both Burxt files, because the check named one.** `conformance.bx` arrived unformatted and this
  # step would not have said so — the same shape as the scopes that were hand-listed elsewhere today.
  run "the Burxt implementation is formatted" bash -c '
    burxt fmt --check burxt/bmx.bx burxt/conformance.bx burxt/guarantees.bx'
  # **The implementation Burxt users get, verified by the language it serves.** `harness.py` above asks
  # the same question in Python and stays exactly what it is — the neutral runner a stranger implementing
  # BMX in a sixth language can use without this toolchain. This one closes the gap that the Burxt
  # implementation was checked only by a program in another language. If the two ever disagree, one of
  # them has a bug and the fixtures are the arbiter.
  run "the suite runs on Burxt, over the Burxt implementation" bash -c '
    burxt build burxt/conformance.bx -o /tmp/check-conformance && /tmp/check-conformance'
  run "the Burxt implementation passes the format's own suite" bash -c '
    burxt build tests/harness.bx -o /tmp/check-harness && /tmp/check-harness /tmp/check-parse'
  run "the two implementations agree with each other" bash -c '
    burxt build tests/agree.bx -o /tmp/check-agree &&
    /tmp/check-agree "node reference/bmx.js" /tmp/check-parse'
  run "no document can reach the output through a target or an info string" bash -c '
    burxt build tools/render.bx -o /tmp/check-render 2>/dev/null &&
    burxt build tests/output.bx -o /tmp/check-output &&
    /tmp/check-output "node reference/bmx.js --render" /tmp/check-render'
  run "the two renderers produce the same page" bash -c '
    burxt build tools/render.bx -o /tmp/check-render &&
    burxt build tests/renders.bx -o /tmp/check-renders && /tmp/check-renders /tmp/check-render'
  # **The escape table in `page.bx` and `errpage.bx` had no instrument pointed at it.** Both were verified
  # byte-identical to the Python they replaced — once, by hand — and then the Python was deleted, so the
  # only oracle went with it. The Burxt session found the same absence in `lib/html_escape`, which had no
  # test of any kind, which is how a one-byte divergence from Python's `html.escape` sat there unexamined:
  # **a byte-level choice with nothing measuring it is a choice nobody knows they made.**
  #
  # The committed panels ARE the oracle: `tools/*.html` are generated, committed, and used to make the
  # screenshots. So this regenerates them and compares. It also converts a discipline `tools/README.md`
  # only asked for — *regenerate whenever the renderer output changes* — into something that fails.
  #
  # **Generated into a temp directory, never in place.** The generators write beside their input, so
  # running them here would overwrite the very files being judged — the sibling-repair shape that made a
  # stale `.vsix` pass on a second run. Inputs are copied out instead, and the tree is untouched: verified
  # by checking `git status` is clean after a run.
  run "the site's rendered panels are what the generators produce" bash -c '
    set -e
    d=$(mktemp -d)
    burxt build tools/render.bx  -o "$d/bmxrender" >/dev/null
    burxt build tools/page.bx    -o "$d/page"      >/dev/null
    burxt build tools/errpage.bx -o "$d/errpage"   >/dev/null
    cp tools/ex1.bmx tools/ex2.bmx tools/ex3.bmx tools/err1.bmx "$d/"
    bad=0
    for n in ex1 ex2 ex3; do
      (cd "$d" && ./page "$n" x >/dev/null)
      cmp -s "$d/$n.html" "tools/$n.html" || { echo "$n.html is not what tools/page.bx produces"; bad=1; }
    done
    (cd "$d" && ./errpage err1 >/dev/null)
    cmp -s "$d/err1.html" "tools/err1.html" || { echo "err1.html is not what tools/errpage.bx produces"; bad=1; }
    burxt build tools/showcase.bx -o "$d/showcase" >/dev/null
    cp tools/shop.bmx "$d/"
    mkdir -p "$d/../docs/_includes"
    (cd "$d" && ./showcase >/dev/null)
    cmp -s "$d/../docs/_includes/showcase.html" "docs/_includes/showcase.html" \
      || { echo "showcase.html is not what tools/showcase.bx produces"; bad=1; }
    rm -rf "$d"
    exit $bad'
  # **And this is the one that costs the most, so it is named rather than slipped in.** The conformance
  # suite itself is run by `tests/harness.bx` now, so nothing in the toolchain-free section runs it. The
  # FORMAT is still testable without Burxt — the fixtures are data and a stranger writes a page of code,
  # which `docs/implementing.md` spells out — but **this repository no longer demonstrates that**, and a
  # property nothing demonstrates is a property nobody can check.
  run "the reference implementation passes the suite" bash -c '
    burxt build tests/harness.bx -o /tmp/check-harness &&
    /tmp/check-harness "node reference/bmx.js"'

  # **Three more checks moved out of the Node-only section as their tools became Burxt**, and the cost is
  # the same one every time: a contributor without a toolchain loses them, and the summary says which
  # groups it skipped rather than printing a smaller total as though it were the suite.
  run "every example is indented the way the format says" bash -c '
    burxt build tools/fmt.bx -o /tmp/check-fmt &&
    /tmp/check-fmt --check docs/*.md docs/guide/*.md README.md editors/vscode/README.md'
  run "indenting a document does not change it" bash -c '
    burxt build tools/fmt.bx -o /tmp/check-fmt &&
    burxt build tests/roundtrip.bx -o /tmp/check-roundtrip &&
    BMX_FMT=/tmp/check-fmt /tmp/check-roundtrip "node reference/bmx.js" &&
    BMX_FMT=/tmp/check-fmt /tmp/check-roundtrip "node reference/bmx.js" --prove-it'

  # **Moved out of the Node-only section, because the server is a Burxt binary now.** That is a real cost
  # and it is the one the reclassification predicted: a contributor without a toolchain loses this check,
  # and the summary says so rather than hiding it in a total.
  run "the language server says what it should, in the right coordinates" bash -c '
    burxt build editors/lsp/bmx-lsp.bx -o /tmp/check-bmx-lsp &&
    burxt build editors/lsp/test/protocol.bx -o /tmp/check-protocol &&
    BMX_LSP=/tmp/check-bmx-lsp /tmp/check-protocol &&
    BMX_LSP=/tmp/check-bmx-lsp /tmp/check-protocol --prove-it'
  run "a document becomes a view the compiler checks" bash -c '
    burxt run burxt/guarantees.bx'
  run "every documented name is reachable, and every public name is documented" bash -c '
    burxt build tests/surface.bx -o /tmp/check-surface &&
    /tmp/check-surface && /tmp/check-surface --prove-it'
  # **The tool `BMX-E036` names had no runner at all**, and its header claimed for a year that a refusal
  # leaves the file alone while the code rewrote it anyway. This check is that claim, plus the one nobody
  # writes down: that the path in a diagnostic is a path that exists.
  # **Out of the documentation group, because measuring a Node floor now needs a Burxt compiler.** The
  # trade is the one every port in this file has made: the check is written in the language this
  # repository is becoming, and a contributor without a toolchain loses it — which the summary says.
  # **This check was in the unguarded group and `ci.yml` had it in the Burxt job** — the drift this
  # file's header exists to prevent, and it hid here because `burxt` happens to be on the author's PATH
  # globally, so the unguarded copy passed locally and would have FAILED on a machine without a
  # toolchain rather than being skipped with the rest. It builds the harness; it belongs where the
  # compiler is. Nothing yet checks that this file and `ci.yml` agree, which is how that lasted.
  run "the invitation on the site is a command that works" bash -c '
    burxt build tests/harness.bx -o /tmp/check-harness &&
    burxt build tests/invitation.bx -o /tmp/check-invitation &&
    BMX_HARNESS=/tmp/check-harness /tmp/check-invitation &&
    BMX_HARNESS=/tmp/check-harness /tmp/check-invitation --prove-it'
  # **Moved out of the unguarded group with its packer.** `editors/vscode/pack.bx` builds the `.vsix`
  # from `lib/zip.bx`, so packaging needs the toolchain now — which is the trade the `gap`
  # reclassification already decided: the format's portability claim is about the FORMAT, and packaging
  # this repository's editor extension was never part of it.
  # **The check that would have caught the three drifts above**, added after the third: `check.sh` and
  # `ci.yml` must run the same checks under the same names. It is in the Burxt group because it is a Burxt
  # program, which means a contributor without a toolchain cannot see the drift — and CI can, which is the
  # half that matters for a file whose subject is CI.
  run "every brand asset carries the family's margin and its own crop" bash -c '
    burxt build tests/branding.bx -o /tmp/check-branding &&
    /tmp/check-branding && /tmp/check-branding --prove-it'
  run "check.sh and ci.yml run the same checks" bash -c '
    burxt build tests/mirror.bx -o /tmp/check-mirror &&
    /tmp/check-mirror && /tmp/check-mirror --prove-it'
  run "the extension's version is the format's, and the committed package is the packed one" bash -c '
    burxt build editors/vscode/pack.bx -o /tmp/check-pack &&
    burxt build tests/extension.bx -o /tmp/check-extension &&
    BMX_PACK=/tmp/check-pack /tmp/check-extension &&
    BMX_PACK=/tmp/check-pack /tmp/check-extension --prove-it'
  run "every file that is not Burxt says why it is not" bash -c '
    burxt build tests/languages.bx -o /tmp/check-languages &&
    /tmp/check-languages && /tmp/check-languages --prove-it'
  run "no runner advertises a control it does not read" bash -c '
    burxt build tests/controls.bx -o /tmp/check-controls &&
    /tmp/check-controls && /tmp/check-controls --prove-it'
  run "every version the documentation states agrees with SPEC.md" bash -c '
    burxt build tests/version.bx -o /tmp/check-version &&
    /tmp/check-version && /tmp/check-version --prove-it'
  run "no refusal tells an author to write what the format refuses" bash -c '
    burxt build tests/messages.bx -o /tmp/check-messages &&
    /tmp/check-messages && /tmp/check-messages --prove-it'
  run "the reference parser needs nothing newer than the Node it promises" bash -c '
    burxt build tests/portability.bx -o /tmp/check-portability &&
    /tmp/check-portability && /tmp/check-portability --prove-it'
  run "the migrator does what its own header says, and E036 names a file that is there" bash -c '
    burxt build tools/migrate-0.7.bx -o /tmp/check-migrate &&
    burxt build tests/migration.bx -o /tmp/check-migration &&
    BMX_MIGRATE=/tmp/check-migrate /tmp/check-migration "node reference/bmx.js" &&
    BMX_MIGRATE=/tmp/check-migrate /tmp/check-migration "node reference/bmx.js" --prove-it'
else
  skip 'the Burxt half needs `burxt` on PATH and BURXT_LIB set — see docs/install.md' \
       "the Burxt half ($(group_size burxt), no toolchain)"
fi

echo
if [ "$fail" -eq 0 ]; then
  printf '\033[32m%d checks passed\033[0m' "$pass"
else
  printf '\033[31m%d failed\033[0m, %d passed' "$fail" "$pass"
fi
if [ "$skipped" -gt 0 ]; then
  printf ', \033[33m%d group(s) skipped\033[0m — %s\n' "$skipped" "$skipped_what"
  printf 'so this run is NOT the suite CI runs; the number above is not comparable to it.\n'
else
  printf ' — the whole suite, nothing skipped\n'
  # **A complete run must account for every `run` line in this file**, which is the arithmetic the note
  # at the top asks a reader to do in their head — 17 + 3 + 9 not adding up to 29 is how the stale label
  # was eventually noticed, months late. Doing it here means a `run` that is never reached, in a block
  # whose guard passed, is a failure rather than a smaller number nobody compares.
  listed=$(grep -c '^ *run ' "${BASH_SOURCE[0]}")
  if [ "$((pass + fail))" -ne "$listed" ]; then
    printf '\033[31mbut this file lists %d checks and ran %d\033[0m — a `run` line was not reached\n' \
      "$listed" "$((pass + fail))"
    exit 1
  fi
fi
exit "$fail"
