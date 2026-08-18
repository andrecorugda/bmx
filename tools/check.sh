#!/usr/bin/env bash
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
run "the reference implementation passes the suite" python3 tests/harness.py "node reference/bmx.js"
run "no refusal tells an author to write what the format refuses" bash -c '
  python3 tests/messages.py && python3 tests/messages.py --prove-it'
run "indenting a document does not change it" bash -c '
  python3 tests/roundtrip.py "node reference/bmx.js" &&
  python3 tests/roundtrip.py "node reference/bmx.js" --prove-it'
run "the suite is not empty" bash -c '[ "$(ls tests/cases/*.bmx | wc -l)" -ge 20 ]'
run "the linter fires where it should and stays quiet where it should" node tests/lints.mjs

echo
echo "the editor surface"
if [ -d editors/vscode/node_modules/vscode-textmate ]; then
  run "the grammar puts every scope where it says it does" node editors/vscode/test/scopes.mjs
  run "the site's colours and the editor's agree" node editors/vscode/test/agrees.mjs
  run "every line is numbered and the document survives painting" bash -c '
    node editors/vscode/test/panel.mjs && node editors/vscode/test/panel.mjs --prove-it'
else
  printf '  \033[33mskip\033[0m  the grammar tests need `cd editors/vscode && npm install vscode-textmate vscode-oniguruma`\n'
fi
run "the editor behaves the way the format reads" node editors/vscode/test/config.mjs
run "the language server says what it should, in the right coordinates" node editors/lsp/test/protocol.mjs
run "the preview does what the button promises" bash -c '
  mkdir -p editors/vscode/reference &&
  cp reference/bmx.js editors/vscode/reference/bmx.mjs &&
  node editors/vscode/test/preview.js'
run "every brand asset carries the family's margin and its own crop" bash -c '
  python3 tests/branding.py && python3 tests/branding.py --prove-it'
run "the extension packages" bash -c '
  python3 editors/vscode/pack.py >/dev/null &&
  python3 -c "
import zipfile, sys
z = zipfile.ZipFile(\"editors/vscode/bmx-0.1.0.vsix\")
need = [\"[Content_Types].xml\", \"extension.vsixmanifest\", \"extension/package.json\",
        \"extension/syntaxes/bmx.tmLanguage.json\", \"extension/icon.png\"]
miss = [n for n in need if n not in z.namelist()]
sys.exit(f\"missing {miss}\") if miss else None
sys.exit(\"corrupt\") if z.testzip() else None
"'

echo
echo "the documentation"
run "every example is indented the way the format says" bash -c '
  python3 tools/fmt.py --check docs/*.md docs/guide/*.md README.md editors/vscode/README.md'
run "every version the documentation states agrees with SPEC.md" bash -c '
  python3 tests/version.py && python3 tests/version.py --prove-it'
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
  echo "the Burxt implementation — needs a released burxt on PATH and BURXT_LIB set"
  run "it compiles" bash -c 'burxt build burxt/examples/parse.bx -o /tmp/check-parse'
  run "it passes the format's own suite" python3 tests/harness.py /tmp/check-parse
  run "the two implementations agree with each other" python3 tests/agree.py 'node reference/bmx.js' /tmp/check-parse
  run "no document can reach the output through a target or an info string" bash -c '
    burxt build tools/render.bx -o /tmp/check-render 2>/dev/null &&
    python3 tests/output.py "node reference/bmx.js --render" /tmp/check-render'
  run "the two renderers produce the same page" bash -c '
    burxt build tools/render.bx -o /tmp/check-render && python3 tests/renders.py /tmp/check-render'
  run "a document becomes a view the compiler checks" python3 burxt/test.py
  run "every documented name is reachable, and every public name is documented" bash -c '
    python3 tests/surface.py && python3 tests/surface.py --prove-it'
else
  printf '  \033[33mskip\033[0m  the Burxt half needs `burxt` on PATH and BURXT_LIB set — see docs/install.md\n'
fi

echo
if [ "$fail" -eq 0 ]; then
  printf '\033[32m%d checks passed\033[0m\n' "$pass"
else
  printf '\033[31m%d failed\033[0m, %d passed\n' "$fail" "$pass"
fi
exit "$fail"
