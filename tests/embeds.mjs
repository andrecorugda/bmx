// not-burxt: platform — the artefact under test, or its runtime, is JavaScript and nothing else can be
// The reference parser imports where there is no `process` — which is every browser.
//
//     node tests/embeds.mjs
//     node tests/embeds.mjs --prove-it     # the negative control
//
// **It did not, and nothing here could see it.** `reference/bmx.js` guarded its CLI block with a bare
// `process.argv[1]`, evaluated when the MODULE is evaluated — so a browser threw
// `ReferenceError: process is not defined` before one export was reachable. Not a broken CLI: a file
// that could not be imported client-side at all. The star-burxt session measured it in a real headless
// browser while building a playground that renders BMX in the page, having reasonably assumed it worked
// because the conformance suite passes. The suite is Node, run from this repository's own root, and so is
// every other exercise this file has ever had.
//
// **`tests/portability.py` is named for exactly this and asks a narrower question** — which Node *syntax*
// floor the file needs. A real question, and the wrong place to stop: a parser offered to strangers to
// copy is portable when it RUNS where they put it, not when its syntax is old enough to. That check could
// have gone green forever on a file no browser could load.
//
// Deleting `globalThis.process` is a fair stand-in and needs no browser in CI: in an ES module `process`
// is a global lookup, so removing it reproduces the browser's ReferenceError exactly. Verified against a
// real headless Chrome before this file was written, which is the only reason to trust the stand-in.
//
// **What it deliberately does NOT assert:** any DOM, any fetch, any bundler. The claim is one thing — the
// module evaluates and its exports work with no Node globals present — because that is the claim a host
// embedding this file depends on, and a bigger claim here would need a browser in CI to keep honest.

const wantFailure = process.argv.includes('--prove-it')

// Captured before the delete, since reporting needs them afterwards.
const { argv, exit, stdout } = process
const say = (s) => stdout.write(s + '\n')

let failures = 0
const check = (name, ok, detail) => {
  say(ok ? `  ok    ${name}` : `  FAIL  ${name}${detail ? '\n          ' + detail : ''}`)
  if (!ok) failures++
}

// The control re-plants the defect rather than pointing the check at something else: a copy of the real
// file with the guard put back the way it was. **A control that tests a different file proves the
// harness runs, not that this check bites** — and the guard is one token, so the copy is the only honest
// way to aim at it.
//
// **Resolved from `import.meta.url`, not from the working directory.** The first draft of this file said
// `'./reference/bmx.js'`, which in an ES module resolves against the MODULE — so it looked for
// `tests/reference/bmx.js` and reported the parser unimportable. It would have "worked" only if run from
// one particular directory, which is the star-burxt session's `./star-generate` defect wearing this
// project's clothes, in the check written to catch that family. Every path here is absolute.
const PARSER = new URL('../reference/bmx.js', import.meta.url)

let target = PARSER.href
if (wantFailure) {
  const { readFileSync, writeFileSync, mkdtempSync } = await import('node:fs')
  const { tmpdir } = await import('node:os')
  const dir = mkdtempSync(tmpdir() + '/bmx-embed-')
  const source = readFileSync(PARSER, 'utf8')
  const broken = source.replace("typeof process !== 'undefined' && process.argv[1]", 'process.argv[1]')
  if (broken === source) {
    say('  FAIL  the control could not find the guard to break — has it been reworded?')
    exit(1)
  }
  writeFileSync(dir + '/bmx.js', broken)
  target = dir + '/bmx.js'
}

delete globalThis.process

let mod = null
let threw = null
try {
  mod = await import(target)
} catch (e) {
  threw = e
}

check('the parser imports with no `process` in the global scope', threw === null,
  threw && String(threw))

if (mod) {
  // Every name a host embedding this file is told it can reach — `docs/install.md` names `parse` and
  // `BmxError`, and a playground needs `render`. An export that exists in Node and not here would be
  // the same defect one layer in.
  for (const name of ['parse', 'render', 'lint', 'at', 'BmxError']) {
    check(`\`${name}\` is reachable there`, typeof mod[name] === 'function')
  }

  // Not just imports — works. Parsing and rendering both, because the CLI block sat between them and a
  // half-evaluated module is the failure mode this is guarding.
  let tree = null
  try { tree = mod.parse('# Hi\n\nTotal: {{ t }}\n') } catch (e) { threw = e }
  check('it parses there', tree && tree.type === 'document' && tree.children.length === 2)

  // **The escaping rule, in the environment where getting it wrong is an XSS rather than a typo.** A
  // playground renders whatever a stranger typed into a page the stranger is looking at.
  let html = null
  try { html = mod.render('Total: {{ t }}\n', { t: '<script>x</script>' }) } catch (e) { html = String(e) }
  check('a slot value is still escaped there',
    typeof html === 'string' && html.includes('&lt;script&gt;') && !html.includes('<script>'),
    html)
}

if (wantFailure) {
  if (failures > 0) { say('\nthe control worked: with the old guard restored, the import fails'); exit(0) }
  say('\nthe control FAILED: a bare `process.argv` guard was importable, so this check proves nothing')
  exit(1)
}

if (failures > 0) { say(`\n${failures} failed`); exit(1) }
say('the parser is embeddable where there is no Node')
